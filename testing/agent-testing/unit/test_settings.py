"""UT-027 — Settings module: environment-driven configuration.

Tests for core/settings.py — all constants are loaded at import/reload time.
Uses importlib.reload() with monkeypatched env vars to test each branch.

Validates:
- RuntimeError raised when ROUTER_USERNAME/PASSWORD are both absent
- USERNAME and PASSWORD loaded from env var fallback (Vault not configured)
- SSH_STRICT_KEY parsed from SSH_STRICT_HOST_KEY env var (default False)
- RESTCONF_PORT parsed from RESTCONF_PORT env var (default 443)
- RESTCONF_VERIFY_TLS parsed from RESTCONF_VERIFY_TLS env var (default False)

Design note: settings.py calls load_dotenv() at module scope which would
repopulate deleted env vars from the .env file. load_dotenv() is patched to a
no-op to keep full control over the test environment.
"""
import importlib
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def _reload_settings(monkeypatch, *, username="admin", password="admin", extra_env=None):
    """Reload core.settings with a clean, controlled environment.

    Patches both load_dotenv() and get_secret() to eliminate any dependency on
    .env file content or Vault connectivity. username/password are the values
    that get_secret() will appear to return.

    Pass username=None and/or password=None to test the RuntimeError guard
    (both missing triggers 'not USERNAME or not PASSWORD').
    """
    # Reset optional env vars to absent, then apply caller overrides
    for var in ("SSH_STRICT_HOST_KEY", "RESTCONF_PORT", "RESTCONF_VERIFY_TLS"):
        monkeypatch.delenv(var, raising=False)
    if extra_env:
        for k, v in extra_env.items():
            monkeypatch.setenv(k, v)

    # Reload with:
    # - load_dotenv patched to no-op (prevents .env repopulating env vars)
    # - get_secret patched to return the caller-specified credential values
    #   (eliminates any dependency on Vault connectivity or env var state)
    import core.settings

    def _mock_get_secret(path, key, fallback_env=""):
        if key == "username":
            return username
        if key == "password":
            return password
        return None

    # Patch core.vault.get_secret (not core.settings.get_secret) — reload re-executes
    # "from core.vault import get_secret", so the patch must be on the source module.
    with patch("core.settings.load_dotenv"), \
         patch("core.vault.get_secret", side_effect=_mock_get_secret):
        return importlib.reload(core.settings)


# ── Credential guard ──────────────────────────────────────────────────────────

class TestSettingsCredentials:
    def test_runtime_error_when_both_creds_missing(self, monkeypatch):
        """Missing USERNAME and PASSWORD must raise RuntimeError at module load."""
        with pytest.raises(RuntimeError, match="ROUTER_USERNAME"):
            _reload_settings(monkeypatch, username=None, password=None)

    def test_runtime_error_when_only_username_missing(self, monkeypatch):
        """Missing USERNAME (with PASSWORD set) must still raise RuntimeError."""
        with pytest.raises(RuntimeError, match="ROUTER_USERNAME"):
            _reload_settings(monkeypatch, username=None, password="pass")

    def test_runtime_error_when_only_password_missing(self, monkeypatch):
        """Missing PASSWORD (with USERNAME set) must still raise RuntimeError."""
        with pytest.raises(RuntimeError, match="ROUTER_USERNAME"):
            _reload_settings(monkeypatch, username="user", password=None)

    def test_creds_loaded_from_env_fallback(self, monkeypatch):
        """When Vault is absent, USERNAME/PASSWORD come from env vars."""
        settings = _reload_settings(monkeypatch, username="netops", password="secret123")
        assert settings.USERNAME == "netops"
        assert settings.PASSWORD == "secret123"


# ── SSH settings ──────────────────────────────────────────────────────────────

class TestSSHSettings:
    def test_ssh_strict_key_default_false(self, monkeypatch):
        """SSH_STRICT_KEY must default to False when env var is absent."""
        settings = _reload_settings(monkeypatch)
        assert settings.SSH_STRICT_KEY is False

    def test_ssh_strict_key_true(self, monkeypatch):
        """SSH_STRICT_HOST_KEY=true must set SSH_STRICT_KEY to True."""
        settings = _reload_settings(monkeypatch, extra_env={"SSH_STRICT_HOST_KEY": "true"})
        assert settings.SSH_STRICT_KEY is True

    def test_ssh_strict_key_false_explicit(self, monkeypatch):
        """SSH_STRICT_HOST_KEY=false must set SSH_STRICT_KEY to False."""
        settings = _reload_settings(monkeypatch, extra_env={"SSH_STRICT_HOST_KEY": "false"})
        assert settings.SSH_STRICT_KEY is False

    def test_ssh_timeout_constants_are_positive(self, monkeypatch):
        """All SSH timeout constants must be positive integers."""
        settings = _reload_settings(monkeypatch)
        assert settings.SSH_TIMEOUT_TRANSPORT > 0
        assert settings.SSH_TIMEOUT_OPS > 0
        assert settings.SSH_TIMEOUT_OPS_LONG > settings.SSH_TIMEOUT_OPS


# ── RESTCONF settings ─────────────────────────────────────────────────────────

class TestRESTCONFSettings:
    def test_restconf_port_default_443(self, monkeypatch):
        """RESTCONF_PORT must default to 443 when env var is absent."""
        settings = _reload_settings(monkeypatch)
        assert settings.RESTCONF_PORT == 443

    def test_restconf_port_custom(self, monkeypatch):
        """RESTCONF_PORT env var must override the default."""
        settings = _reload_settings(monkeypatch, extra_env={"RESTCONF_PORT": "8443"})
        assert settings.RESTCONF_PORT == 8443

    def test_restconf_verify_tls_default_false(self, monkeypatch):
        """RESTCONF_VERIFY_TLS must default to False when env var is absent."""
        settings = _reload_settings(monkeypatch)
        assert settings.RESTCONF_VERIFY_TLS is False

    def test_restconf_verify_tls_true(self, monkeypatch):
        """RESTCONF_VERIFY_TLS=true must set RESTCONF_VERIFY_TLS to True."""
        settings = _reload_settings(monkeypatch, extra_env={"RESTCONF_VERIFY_TLS": "true"})
        assert settings.RESTCONF_VERIFY_TLS is True
