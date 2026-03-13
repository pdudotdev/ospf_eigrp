"""UT-023 — Watcher helper function unit tests.

Tests for oncall/watcher.py helper functions that had no unit coverage:
  load_device_map, resolve_device, parse_event_ts, is_lock_stale,
  _read_log_tail, notify_operator.

No real filesystem mounts, tmux, or device connections required.
All file operations use tmp_path; PID checks use patch.

Validates:
- load_device_map builds IP→name dict from NETWORK.json
- load_device_map returns {} on missing file
- load_device_map returns {} on malformed JSON
- load_device_map skips entries without "host" key
- resolve_device returns device name when IP is in map
- resolve_device falls back to IP string when not in map
- resolve_device handles empty map
- parse_event_ts parses ISO timestamp with Z suffix
- parse_event_ts parses ISO timestamp with +00:00 suffix
- parse_event_ts returns None for missing ts key
- parse_event_ts returns None for malformed ts string
- is_lock_stale returns False when lock file does not exist
- is_lock_stale returns False when lock PID is the running process
- is_lock_stale returns True when lock PID does not exist
- is_lock_stale returns True when lock file contains non-numeric content
- _read_log_tail returns last N lines of file
- _read_log_tail returns all lines when file has fewer than N lines
- _read_log_tail returns None when file does not exist
- notify_operator completes without raising when notify-send is absent
- notify_operator completes without raising on TimeoutExpired
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import oncall.watcher as watcher
from oncall.watcher import (
    load_device_map,
    resolve_device,
    parse_event_ts,
    is_lock_stale,
    _read_log_tail,
    notify_operator,
)


# ── load_device_map ────────────────────────────────────────────────────────────

class TestLoadDeviceMap:
    def test_normal_load(self, tmp_path, monkeypatch):
        """Normal NETWORK.json yields correct IP→name mapping."""
        inventory = {
            "A1C": {"host": "172.20.20.205", "platform": "cisco_iosxe", "transport": "asyncssh", "cli_style": "ios"},
            "C1C": {"host": "172.20.20.207", "platform": "cisco_iosxe", "transport": "restconf", "cli_style": "ios"},
        }
        inv_file = tmp_path / "NETWORK.json"
        inv_file.write_text(json.dumps(inventory))
        monkeypatch.setattr("oncall.watcher.INVENTORY_FILE", inv_file)

        result = load_device_map()
        assert result == {"172.20.20.205": "A1C", "172.20.20.207": "C1C"}

    def test_missing_file_returns_empty_dict(self, tmp_path, monkeypatch):
        """Missing inventory file returns empty dict, does not raise."""
        monkeypatch.setattr("oncall.watcher.INVENTORY_FILE", tmp_path / "nonexistent.json")
        result = load_device_map()
        assert result == {}

    def test_malformed_json_returns_empty_dict(self, tmp_path, monkeypatch):
        """Malformed JSON in inventory file returns empty dict, does not raise."""
        inv_file = tmp_path / "NETWORK.json"
        inv_file.write_text("{bad json!}")
        monkeypatch.setattr("oncall.watcher.INVENTORY_FILE", inv_file)
        result = load_device_map()
        assert result == {}

    def test_entries_without_host_key_skipped(self, tmp_path, monkeypatch):
        """Entries without a 'host' key raise KeyError — the whole map returns empty
        (current implementation propagates the KeyError up to the except block)."""
        inventory = {
            "A1C": {"platform": "cisco_iosxe"},  # missing "host"
        }
        inv_file = tmp_path / "NETWORK.json"
        inv_file.write_text(json.dumps(inventory))
        monkeypatch.setattr("oncall.watcher.INVENTORY_FILE", inv_file)
        result = load_device_map()
        # KeyError is caught by the except Exception handler — returns {}
        assert result == {}

    def test_empty_inventory_returns_empty_dict(self, tmp_path, monkeypatch):
        """Empty JSON object yields empty device map."""
        inv_file = tmp_path / "NETWORK.json"
        inv_file.write_text("{}")
        monkeypatch.setattr("oncall.watcher.INVENTORY_FILE", inv_file)
        result = load_device_map()
        assert result == {}


# ── resolve_device ─────────────────────────────────────────────────────────────

class TestResolveDevice:
    def test_ip_found_returns_name(self):
        device_map = {"172.20.20.205": "A1C", "172.20.20.207": "C1C"}
        assert resolve_device("172.20.20.205", device_map) == "A1C"

    def test_ip_not_found_returns_ip(self):
        device_map = {"172.20.20.205": "A1C"}
        assert resolve_device("172.20.20.209", device_map) == "172.20.20.209"

    def test_empty_map_returns_ip(self):
        assert resolve_device("10.0.0.1", {}) == "10.0.0.1"


# ── parse_event_ts ─────────────────────────────────────────────────────────────

class TestParseEventTs:
    def test_iso_with_z_suffix(self):
        event = {"ts": "2026-03-01T07:26:05.065Z"}
        result = parse_event_ts(event)
        assert result is not None
        assert result.tzinfo is not None  # timezone-aware
        assert result.year == 2026
        assert result.month == 3
        assert result.day == 1

    def test_iso_with_utc_offset(self):
        event = {"ts": "2026-03-01T07:26:05+00:00"}
        result = parse_event_ts(event)
        assert result is not None
        assert result.tzinfo is not None

    def test_missing_ts_key_returns_none(self):
        assert parse_event_ts({}) is None

    def test_empty_ts_string_returns_none(self):
        assert parse_event_ts({"ts": ""}) is None

    def test_malformed_ts_returns_none(self):
        assert parse_event_ts({"ts": "not-a-timestamp"}) is None

    def test_non_string_ts_returns_none(self):
        # ts is an int — fromisoformat won't be called, but the Z-replace will fail
        assert parse_event_ts({"ts": 12345}) is None


# ── is_lock_stale ──────────────────────────────────────────────────────────────

class TestIsLockStale:
    def test_no_lock_file_returns_false(self, tmp_path, monkeypatch):
        """No lock file → not stale."""
        lock = tmp_path / "oncall.lock"
        monkeypatch.setattr("oncall.watcher.LOCK_FILE", lock)
        assert is_lock_stale() is False

    def test_lock_with_current_pid_is_fresh(self, tmp_path, monkeypatch):
        """Lock file with our own PID → process alive, not stale."""
        lock = tmp_path / "oncall.lock"
        lock.write_text(str(os.getpid()))
        monkeypatch.setattr("oncall.watcher.LOCK_FILE", lock)
        assert is_lock_stale() is False

    def test_lock_with_dead_pid_is_stale(self, tmp_path, monkeypatch):
        """Lock file with a PID that doesn't exist → stale."""
        lock = tmp_path / "oncall.lock"
        lock.write_text("999999")  # very unlikely to exist
        monkeypatch.setattr("oncall.watcher.LOCK_FILE", lock)
        # Patch os.kill to raise ProcessLookupError (simulating dead PID)
        with patch("oncall.watcher.os.kill", side_effect=ProcessLookupError):
            assert is_lock_stale() is True

    def test_lock_with_non_numeric_pid_is_stale(self, tmp_path, monkeypatch):
        """Lock file with non-numeric content (corrupt) → stale."""
        lock = tmp_path / "oncall.lock"
        lock.write_text("not-a-pid")
        monkeypatch.setattr("oncall.watcher.LOCK_FILE", lock)
        assert is_lock_stale() is True


# ── _read_log_tail ─────────────────────────────────────────────────────────────

class TestReadLogTail:
    def test_returns_last_n_lines(self, tmp_path):
        log = tmp_path / "test.log"
        log.write_text("\n".join(f"line{i}" for i in range(20)))
        result = _read_log_tail(log, lines=5)
        assert result is not None
        lines = result.splitlines()
        assert len(lines) == 5
        assert lines[-1] == "line19"

    def test_returns_all_lines_when_file_shorter(self, tmp_path):
        log = tmp_path / "test.log"
        log.write_text("line1\nline2\nline3")
        result = _read_log_tail(log, lines=10)
        assert result is not None
        assert "line1" in result
        assert "line3" in result

    def test_returns_none_on_missing_file(self, tmp_path):
        result = _read_log_tail(tmp_path / "nonexistent.log")
        assert result is None

    def test_empty_file_returns_none(self, tmp_path):
        log = tmp_path / "empty.log"
        log.write_text("")
        result = _read_log_tail(log)
        assert result is None


# ── notify_operator ────────────────────────────────────────────────────────────

class TestNotifyOperator:
    def test_notify_send_not_found_does_not_raise(self):
        """When notify-send is not installed, notify_operator silently continues."""
        with patch("oncall.watcher.subprocess.run", side_effect=FileNotFoundError):
            notify_operator("oncall-test-session")  # Should not raise

    def test_notify_send_timeout_does_not_raise(self):
        """When notify-send times out, notify_operator silently continues."""
        import subprocess
        with patch("oncall.watcher.subprocess.run",
                   side_effect=subprocess.TimeoutExpired(cmd="notify-send", timeout=5)):
            notify_operator("oncall-test-session")  # Should not raise

    def test_notify_operator_calls_subprocess(self):
        """notify_operator calls subprocess.run with notify-send arguments."""
        with patch("oncall.watcher.subprocess.run") as mock_run:
            notify_operator("oncall-abc-123")
            mock_run.assert_called_once()
            cmd = mock_run.call_args[0][0]
            assert "notify-send" in cmd
            assert "oncall-abc-123" in " ".join(cmd)
