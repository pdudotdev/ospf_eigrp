"""UT-025 — Logging configuration unit tests.

Tests for core/logging_config.py: JSONFormatter, setup_logging, setup_watcher_logging.

Validates:
- JSONFormatter.format() produces valid JSON with required fields
- JSONFormatter includes exception info when exc_info is set
- JSONFormatter includes extra fields passed via extra={...}
- setup_logging() is idempotent (calling twice adds only one handler)
- setup_logging() respects LOG_LEVEL env var
- setup_watcher_logging() adds a RotatingFileHandler to ainoc.watcher
- setup_watcher_logging() is idempotent (second call adds no duplicate handler)
"""
import json
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.logging_config import JSONFormatter, setup_logging, setup_watcher_logging


def _fresh_logger(name: str) -> logging.Logger:
    """Return a logger with all handlers removed and propagation restored (isolated for testing)."""
    log = logging.getLogger(name)
    log.handlers.clear()
    log.propagate = True  # Restore default so other tests can use caplog
    log.level = logging.WARNING  # Reset to default level
    return log


# ── JSONFormatter ──────────────────────────────────────────────────────────────

class TestJSONFormatter:
    def _make_record(self, msg="test message", level=logging.INFO, name="test.logger",
                     exc_info=None, **extra):
        record = logging.LogRecord(
            name=name, level=level, pathname="x.py",
            lineno=1, msg=msg, args=(), exc_info=exc_info,
        )
        for k, v in extra.items():
            setattr(record, k, v)
        return record

    def test_produces_valid_json(self):
        fmt = JSONFormatter()
        record = self._make_record()
        output = fmt.format(record)
        parsed = json.loads(output)  # Must not raise
        assert isinstance(parsed, dict)

    def test_required_fields_present(self):
        fmt = JSONFormatter()
        record = self._make_record(msg="hello world")
        parsed = json.loads(fmt.format(record))
        assert "ts" in parsed
        assert "level" in parsed
        assert "logger" in parsed
        assert "msg" in parsed

    def test_message_content(self):
        fmt = JSONFormatter()
        record = self._make_record(msg="SLA path A1C_TO_IAN is down")
        parsed = json.loads(fmt.format(record))
        assert parsed["msg"] == "SLA path A1C_TO_IAN is down"

    def test_level_name(self):
        fmt = JSONFormatter()
        record = self._make_record(level=logging.WARNING)
        parsed = json.loads(fmt.format(record))
        assert parsed["level"] == "WARNING"

    def test_exc_field_present_when_exception_set(self):
        fmt = JSONFormatter()
        try:
            raise ValueError("test error")
        except ValueError:
            import sys as _sys
            exc_info = _sys.exc_info()
        record = self._make_record(exc_info=exc_info)
        parsed = json.loads(fmt.format(record))
        assert "exc" in parsed
        assert "ValueError" in parsed["exc"]

    def test_extra_fields_forwarded(self):
        fmt = JSONFormatter()
        record = self._make_record(device_name="A1C", session_id="abc")
        parsed = json.loads(fmt.format(record))
        assert parsed.get("device_name") == "A1C"
        assert parsed.get("session_id") == "abc"

    def test_timestamp_format(self):
        fmt = JSONFormatter()
        record = self._make_record()
        parsed = json.loads(fmt.format(record))
        # Should be ISO-8601 UTC: "2026-03-01T07:26:05.065Z"
        ts = parsed["ts"]
        assert ts.endswith("Z")
        assert "T" in ts


# ── setup_logging ──────────────────────────────────────────────────────────────

class TestSetupLogging:
    def setup_method(self):
        """Clear the 'ainoc' logger handlers before each test."""
        _fresh_logger("ainoc")

    def teardown_method(self):
        """Restore 'ainoc' logger to clean state after each test so other test files are unaffected."""
        _fresh_logger("ainoc")

    def test_adds_one_stderr_handler(self):
        setup_logging()
        root = logging.getLogger("ainoc")
        assert len(root.handlers) == 1

    def test_idempotent_second_call_no_duplicate(self):
        setup_logging()
        setup_logging()  # Second call must be a no-op
        root = logging.getLogger("ainoc")
        assert len(root.handlers) == 1

    def test_respects_log_level_debug(self, monkeypatch):
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        setup_logging()
        root = logging.getLogger("ainoc")
        assert root.level == logging.DEBUG

    def test_respects_log_level_warning(self, monkeypatch):
        monkeypatch.setenv("LOG_LEVEL", "WARNING")
        setup_logging()
        root = logging.getLogger("ainoc")
        assert root.level == logging.WARNING


# ── setup_watcher_logging ──────────────────────────────────────────────────────

class TestSetupWatcherLogging:
    def setup_method(self):
        """Clear handlers from ainoc and ainoc.watcher before each test."""
        _fresh_logger("ainoc")
        _fresh_logger("ainoc.watcher")

    def teardown_method(self):
        """Restore loggers to clean state after each test so other test files are unaffected."""
        _fresh_logger("ainoc")
        _fresh_logger("ainoc.watcher")

    def test_adds_rotating_file_handler(self, tmp_path):
        log_file = tmp_path / "watcher.log"
        setup_watcher_logging(log_file)
        watcher_log = logging.getLogger("ainoc.watcher")
        file_handlers = [h for h in watcher_log.handlers if isinstance(h, RotatingFileHandler)]
        assert len(file_handlers) == 1

    def test_creates_parent_directory(self, tmp_path):
        log_file = tmp_path / "logs" / "watcher.log"
        assert not log_file.parent.exists()
        setup_watcher_logging(log_file)
        assert log_file.parent.exists()

    def test_idempotent_second_call_no_duplicate(self, tmp_path):
        log_file = tmp_path / "watcher.log"
        setup_watcher_logging(log_file)
        setup_watcher_logging(log_file)  # Second call must be a no-op
        watcher_log = logging.getLogger("ainoc.watcher")
        file_handlers = [h for h in watcher_log.handlers if isinstance(h, RotatingFileHandler)]
        assert len(file_handlers) == 1
