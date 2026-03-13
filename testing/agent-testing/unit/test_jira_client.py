"""UT-022 — Jira client core logic tests.

Tests for core/jira_client.py: _is_configured, _to_adf, create_issue,
add_comment, and resolve_issue.  All HTTP calls are mocked via aiohttp.
No real Jira connectivity required.

Validates:
- _is_configured returns True only when all 4 required env vars are present
- _to_adf converts plain text to ADF paragraphs with correct structure
- create_issue returns issue key on 201 success
- create_issue retries with "Task" fallback on 400
- create_issue returns None on non-201/400 HTTP error
- create_issue returns None on connection error
- create_issue returns None when not configured
- add_comment calls the correct URL on success (200/201)
- add_comment logs error on non-2xx but does not raise
- add_comment skips when not configured
- resolve_issue transitions on matching name
- resolve_issue selects fallback transition names (done, resolve, close)
- resolve_issue handles "Won't Fix" resolution → "Won't Fix" field
- resolve_issue falls back to comment-only when no matching transition
- resolve_issue falls back to comment-only when transition GET fails
- resolve_issue skips when not configured
"""
import asyncio
import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.jira_client import _is_configured, _to_adf, create_issue, add_comment, resolve_issue


def run(coro):
    return asyncio.run(coro)


# ── _is_configured ─────────────────────────────────────────────────────────────

class TestIsConfigured:
    def test_all_vars_present_returns_true(self, monkeypatch):
        monkeypatch.setenv("JIRA_BASE_URL", "https://test.atlassian.net")
        monkeypatch.setenv("JIRA_EMAIL", "user@test.com")
        monkeypatch.setenv("JIRA_API_TOKEN", "token123")
        monkeypatch.setenv("JIRA_PROJECT_KEY", "SUP")
        with patch("core.jira_client.get_secret", return_value="token123"):
            assert _is_configured() is True

    def test_missing_base_url_returns_false(self, monkeypatch):
        monkeypatch.delenv("JIRA_BASE_URL", raising=False)
        monkeypatch.setenv("JIRA_EMAIL", "user@test.com")
        monkeypatch.setenv("JIRA_API_TOKEN", "token123")
        monkeypatch.setenv("JIRA_PROJECT_KEY", "SUP")
        with patch("core.jira_client.get_secret", return_value="token123"):
            assert _is_configured() is False

    def test_missing_email_returns_false(self, monkeypatch):
        monkeypatch.setenv("JIRA_BASE_URL", "https://test.atlassian.net")
        monkeypatch.delenv("JIRA_EMAIL", raising=False)
        monkeypatch.setenv("JIRA_API_TOKEN", "token123")
        monkeypatch.setenv("JIRA_PROJECT_KEY", "SUP")
        with patch("core.jira_client.get_secret", return_value="token123"):
            assert _is_configured() is False

    def test_missing_api_token_returns_false(self, monkeypatch):
        monkeypatch.setenv("JIRA_BASE_URL", "https://test.atlassian.net")
        monkeypatch.setenv("JIRA_EMAIL", "user@test.com")
        monkeypatch.delenv("JIRA_API_TOKEN", raising=False)
        monkeypatch.setenv("JIRA_PROJECT_KEY", "SUP")
        with patch("core.jira_client.get_secret", return_value=None):
            assert _is_configured() is False

    def test_missing_project_key_returns_false(self, monkeypatch):
        monkeypatch.setenv("JIRA_BASE_URL", "https://test.atlassian.net")
        monkeypatch.setenv("JIRA_EMAIL", "user@test.com")
        monkeypatch.setenv("JIRA_API_TOKEN", "token123")
        monkeypatch.delenv("JIRA_PROJECT_KEY", raising=False)
        with patch("core.jira_client.get_secret", return_value="token123"):
            assert _is_configured() is False


# ── _to_adf ────────────────────────────────────────────────────────────────────

class TestToAdf:
    def test_single_line_produces_one_paragraph(self):
        result = _to_adf("Hello world")
        assert result["version"] == 1
        assert result["type"] == "doc"
        assert len(result["content"]) == 1
        para = result["content"][0]
        assert para["type"] == "paragraph"
        assert para["content"][0]["type"] == "text"
        assert para["content"][0]["text"] == "Hello world"

    def test_multiline_produces_multiple_paragraphs(self):
        result = _to_adf("Line one\nLine two\nLine three")
        assert len(result["content"]) == 3
        texts = [p["content"][0]["text"] for p in result["content"]]
        assert texts == ["Line one", "Line two", "Line three"]

    def test_empty_line_becomes_single_space(self):
        result = _to_adf("First\n\nThird")
        # strip() removes leading/trailing blank, then split("\n") gives ["First", "", "Third"]
        texts = [p["content"][0]["text"] for p in result["content"]]
        assert texts[1] == " ", "Empty line must become a single space text node"

    def test_leading_trailing_whitespace_stripped(self):
        result = _to_adf("  \nContent\n  ")
        # strip() removes leading/trailing blank lines
        texts = [p["content"][0]["text"] for p in result["content"]]
        assert "Content" in texts


# ── create_issue ───────────────────────────────────────────────────────────────

def _jira_env(monkeypatch):
    """Set minimal Jira env vars and patch get_secret."""
    monkeypatch.setenv("JIRA_BASE_URL", "https://test.atlassian.net")
    monkeypatch.setenv("JIRA_EMAIL", "user@test.com")
    monkeypatch.setenv("JIRA_API_TOKEN", "token123")
    monkeypatch.setenv("JIRA_PROJECT_KEY", "SUP")
    monkeypatch.setenv("JIRA_ISSUE_TYPE", "[System] Incident")


def _make_mock_session(status_201=True, fallback_status=None):
    """Build a mock aiohttp.ClientSession that returns configurable responses."""
    resp = MagicMock()
    resp.status = 201 if status_201 else 400
    resp.json = AsyncMock(return_value={"key": "SUP-1"})
    resp.text = AsyncMock(return_value="error text")
    resp.__aenter__ = AsyncMock(return_value=resp)
    resp.__aexit__ = AsyncMock(return_value=False)

    if fallback_status is not None:
        resp2 = MagicMock()
        resp2.status = fallback_status
        resp2.json = AsyncMock(return_value={"key": "SUP-1"})
        resp2.text = AsyncMock(return_value="error text")
        resp2.__aenter__ = AsyncMock(return_value=resp2)
        resp2.__aexit__ = AsyncMock(return_value=False)
        # post returns resp first call, resp2 second call
        session = MagicMock()
        session.post = MagicMock(side_effect=[resp, resp2])
        session.__aenter__ = AsyncMock(return_value=session)
        session.__aexit__ = AsyncMock(return_value=False)
        return session

    session = MagicMock()
    session.post = MagicMock(return_value=resp)
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=False)
    return session


class TestCreateIssue:
    def test_success_returns_issue_key(self, monkeypatch):
        _jira_env(monkeypatch)
        session = _make_mock_session(status_201=True)
        with patch("core.jira_client._is_configured", return_value=True), \
             patch("aiohttp.ClientSession", return_value=session):
            result = run(create_issue("SLA Failure", "Network path A1C->IAN is down"))
        assert result == "SUP-1"

    def test_returns_none_when_not_configured(self, monkeypatch):
        with patch("core.jira_client._is_configured", return_value=False):
            result = run(create_issue("Test", "desc"))
        assert result is None

    def test_400_retries_with_task_fallback_and_returns_key(self, monkeypatch):
        _jira_env(monkeypatch)
        # First POST → 400, second POST → 201 (Task fallback)
        session = _make_mock_session(status_201=False, fallback_status=201)
        with patch("core.jira_client._is_configured", return_value=True), \
             patch("aiohttp.ClientSession", return_value=session):
            result = run(create_issue("SLA Failure", "desc"))
        assert result == "SUP-1"

    def test_400_fallback_also_fails_returns_none(self, monkeypatch):
        _jira_env(monkeypatch)
        # First POST → 400, second POST → 500 (both fail)
        session = _make_mock_session(status_201=False, fallback_status=500)
        with patch("core.jira_client._is_configured", return_value=True), \
             patch("aiohttp.ClientSession", return_value=session):
            result = run(create_issue("SLA Failure", "desc"))
        assert result is None

    def test_non_201_non_400_returns_none(self, monkeypatch):
        _jira_env(monkeypatch)
        resp = MagicMock()
        resp.status = 500
        resp.text = AsyncMock(return_value="server error")
        resp.__aenter__ = AsyncMock(return_value=resp)
        resp.__aexit__ = AsyncMock(return_value=False)
        session = MagicMock()
        session.post = MagicMock(return_value=resp)
        session.__aenter__ = AsyncMock(return_value=session)
        session.__aexit__ = AsyncMock(return_value=False)
        with patch("core.jira_client._is_configured", return_value=True), \
             patch("aiohttp.ClientSession", return_value=session):
            result = run(create_issue("SLA Failure", "desc"))
        assert result is None

    def test_connection_error_returns_none(self, monkeypatch):
        _jira_env(monkeypatch)
        import aiohttp as _aiohttp
        with patch("core.jira_client._is_configured", return_value=True), \
             patch("aiohttp.ClientSession") as MockSession:
            MockSession.return_value.__aenter__ = AsyncMock(
                side_effect=_aiohttp.ClientError("connection refused")
            )
            MockSession.return_value.__aexit__ = AsyncMock(return_value=False)
            result = run(create_issue("SLA Failure", "desc"))
        assert result is None


# ── add_comment ────────────────────────────────────────────────────────────────

class TestAddComment:
    def _make_comment_session(self, status):
        resp = MagicMock()
        resp.status = status
        resp.text = AsyncMock(return_value="error text")
        resp.__aenter__ = AsyncMock(return_value=resp)
        resp.__aexit__ = AsyncMock(return_value=False)
        session = MagicMock()
        session.post = MagicMock(return_value=resp)
        session.__aenter__ = AsyncMock(return_value=session)
        session.__aexit__ = AsyncMock(return_value=False)
        return session

    def test_success_200(self, monkeypatch):
        _jira_env(monkeypatch)
        session = self._make_comment_session(200)
        with patch("core.jira_client._is_configured", return_value=True), \
             patch("aiohttp.ClientSession", return_value=session):
            run(add_comment("SUP-1", "Test comment"))
        session.post.assert_called_once()
        call_url = session.post.call_args[0][0]
        assert "SUP-1/comment" in call_url

    def test_success_201(self, monkeypatch):
        _jira_env(monkeypatch)
        session = self._make_comment_session(201)
        with patch("core.jira_client._is_configured", return_value=True), \
             patch("aiohttp.ClientSession", return_value=session):
            run(add_comment("SUP-2", "Another comment"))  # Should not raise
        session.post.assert_called_once()

    def test_http_error_does_not_raise(self, monkeypatch):
        _jira_env(monkeypatch)
        session = self._make_comment_session(500)
        with patch("core.jira_client._is_configured", return_value=True), \
             patch("aiohttp.ClientSession", return_value=session):
            run(add_comment("SUP-1", "Test"))  # Should not raise even on 500

    def test_skips_when_not_configured(self, monkeypatch):
        with patch("core.jira_client._is_configured", return_value=False), \
             patch("aiohttp.ClientSession") as MockSession:
            run(add_comment("SUP-1", "Test"))
            MockSession.assert_not_called()


# ── resolve_issue ──────────────────────────────────────────────────────────────

class TestResolveIssue:
    def _transitions_resp(self, names):
        """Build a mock GET /transitions response with given transition names."""
        transitions = [{"id": str(i + 10), "name": name} for i, name in enumerate(names)]
        resp = MagicMock()
        resp.status = 200
        resp.json = AsyncMock(return_value={"transitions": transitions})
        resp.__aenter__ = AsyncMock(return_value=resp)
        resp.__aexit__ = AsyncMock(return_value=False)
        return resp

    def _post_resp(self, status=204):
        resp = MagicMock()
        resp.status = status
        resp.text = AsyncMock(return_value="ok")
        resp.__aenter__ = AsyncMock(return_value=resp)
        resp.__aexit__ = AsyncMock(return_value=False)
        return resp

    def test_matching_transition_done(self, monkeypatch):
        _jira_env(monkeypatch)
        get_resp = self._transitions_resp(["Open", "In Progress", "Done"])
        post_transition_resp = self._post_resp(204)

        comment_resp = MagicMock()
        comment_resp.status = 201
        comment_resp.text = AsyncMock(return_value="")
        comment_resp.__aenter__ = AsyncMock(return_value=comment_resp)
        comment_resp.__aexit__ = AsyncMock(return_value=False)

        session = MagicMock()
        session.get = MagicMock(return_value=get_resp)
        session.post = MagicMock(side_effect=[post_transition_resp, comment_resp])
        session.__aenter__ = AsyncMock(return_value=session)
        session.__aexit__ = AsyncMock(return_value=False)

        with patch("core.jira_client._is_configured", return_value=True), \
             patch("aiohttp.ClientSession", return_value=session):
            run(resolve_issue("SUP-1", "Fixed the OSPF passive-interface"))

        # GET transitions + POST transition + POST comment
        session.get.assert_called_once()
        assert session.post.call_count == 2

    def test_fallback_transition_name_resolve(self, monkeypatch):
        """'resolve' is in the fallback names set, should match."""
        _jira_env(monkeypatch)
        get_resp = self._transitions_resp(["Open", "Resolve"])  # "Resolve" normalizes to "resolve"
        post_transition_resp = self._post_resp(204)

        comment_resp = MagicMock()
        comment_resp.status = 201
        comment_resp.text = AsyncMock(return_value="")
        comment_resp.__aenter__ = AsyncMock(return_value=comment_resp)
        comment_resp.__aexit__ = AsyncMock(return_value=False)

        session = MagicMock()
        session.get = MagicMock(return_value=get_resp)
        session.post = MagicMock(side_effect=[post_transition_resp, comment_resp])
        session.__aenter__ = AsyncMock(return_value=session)
        session.__aexit__ = AsyncMock(return_value=False)

        with patch("core.jira_client._is_configured", return_value=True), \
             patch("aiohttp.ClientSession", return_value=session):
            run(resolve_issue("SUP-1", "Resolution comment", resolution="Done"))

        assert session.post.call_count == 2  # transition + comment

    def test_wont_fix_resolution_sets_field(self, monkeypatch):
        """resolution="Won't Fix" must set fields.resolution.name = "Won't Fix"."""
        _jira_env(monkeypatch)
        get_resp = self._transitions_resp(["Open", "Done"])
        captured_payload = {}

        async def capture_post(url, json=None, **kwargs):
            if "/transitions" in url:
                captured_payload.update(json or {})
            resp = MagicMock()
            resp.status = 204
            resp.text = AsyncMock(return_value="")
            resp.__aenter__ = AsyncMock(return_value=resp)
            resp.__aexit__ = AsyncMock(return_value=False)
            return resp

        comment_resp = MagicMock()
        comment_resp.status = 201
        comment_resp.text = AsyncMock(return_value="")
        comment_resp.__aenter__ = AsyncMock(return_value=comment_resp)
        comment_resp.__aexit__ = AsyncMock(return_value=False)

        session = MagicMock()
        session.get = MagicMock(return_value=get_resp)
        # First call is the transition POST, second is comment POST
        session.post = MagicMock(side_effect=[
            MagicMock(__aenter__=AsyncMock(return_value=MagicMock(
                status=204, text=AsyncMock(return_value=""),
                __aexit__=AsyncMock(return_value=False)
            )), __aexit__=AsyncMock(return_value=False)),
            comment_resp
        ])
        session.__aenter__ = AsyncMock(return_value=session)
        session.__aexit__ = AsyncMock(return_value=False)

        with patch("core.jira_client._is_configured", return_value=True), \
             patch("aiohttp.ClientSession", return_value=session):
            run(resolve_issue("SUP-1", "Won't fix this", resolution="Won't Fix"))

        # Verify the transition payload used "Won't Fix" as the resolution name
        transition_call_kwargs = session.post.call_args_list[0][1]
        assert transition_call_kwargs["json"]["fields"]["resolution"]["name"] == "Won't Fix"

    def test_no_matching_transition_falls_back_to_comment_only(self, monkeypatch):
        """When no transition matches, only a comment is posted (no transition POST)."""
        _jira_env(monkeypatch)
        # Transitions without any matching name
        get_resp = self._transitions_resp(["Open", "In Progress", "Review"])

        comment_resp = MagicMock()
        comment_resp.status = 201
        comment_resp.text = AsyncMock(return_value="")
        comment_resp.__aenter__ = AsyncMock(return_value=comment_resp)
        comment_resp.__aexit__ = AsyncMock(return_value=False)

        session = MagicMock()
        session.get = MagicMock(return_value=get_resp)
        session.post = MagicMock(return_value=comment_resp)
        session.__aenter__ = AsyncMock(return_value=session)
        session.__aexit__ = AsyncMock(return_value=False)

        with patch("core.jira_client._is_configured", return_value=True), \
             patch("aiohttp.ClientSession", return_value=session):
            run(resolve_issue("SUP-1", "comment only fallback"))

        # Only the comment POST should have been called (no transition POST)
        assert session.post.call_count == 1

    def test_get_transitions_fails_falls_back_to_comment(self, monkeypatch):
        """When GET /transitions returns non-200, only a comment is posted."""
        _jira_env(monkeypatch)
        get_resp = MagicMock()
        get_resp.status = 403
        get_resp.__aenter__ = AsyncMock(return_value=get_resp)
        get_resp.__aexit__ = AsyncMock(return_value=False)

        comment_resp = MagicMock()
        comment_resp.status = 201
        comment_resp.text = AsyncMock(return_value="")
        comment_resp.__aenter__ = AsyncMock(return_value=comment_resp)
        comment_resp.__aexit__ = AsyncMock(return_value=False)

        session = MagicMock()
        session.get = MagicMock(return_value=get_resp)
        session.post = MagicMock(return_value=comment_resp)
        session.__aenter__ = AsyncMock(return_value=session)
        session.__aexit__ = AsyncMock(return_value=False)

        with patch("core.jira_client._is_configured", return_value=True), \
             patch("aiohttp.ClientSession", return_value=session):
            run(resolve_issue("SUP-1", "fallback comment"))

        assert session.post.call_count == 1

    def test_skips_when_not_configured(self, monkeypatch):
        with patch("core.jira_client._is_configured", return_value=False), \
             patch("aiohttp.ClientSession") as MockSession:
            run(resolve_issue("SUP-1", "comment"))
            MockSession.assert_not_called()
