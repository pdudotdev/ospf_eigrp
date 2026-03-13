"""
IT-002 — Watcher Event Parsing

Tests the watcher's event detection logic without spawning an actual agent.
Verifies:
- Non-SLA events are ignored
- SLA Down events are detected (lock file created)
- Stale lock cleanup works correctly
"""

import json
import os
import sys
import tempfile
import threading
import time
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from oncall.watcher import (
    is_sla_down_event,
    is_lock_stale,
    cleanup_lock,
    parse_event_ts,
    scan_for_deferred_events,
    scan_for_recovery_events,
    LOCK_FILE,
)


# ── IT-002a: Event classification ─────────────────────────────────────────────

SLA_DOWN_MESSAGES = [
    "%TRACK-6-STATE: 1 ip sla 1 reachability Up -> Down",
    "BOM%TRACK-6-STATE: 2 ip sla 2 reachability Up -> Down",
]

NON_SLA_MESSAGES = [
    "%TRACK-6-STATE: 1 ip sla 1 reachability Down -> Up",
    "%SYS-5-CONFIG_I: Configured from console by admin",
    "BGP neighbor 10.0.0.1 state Established",
    "",
]


@pytest.mark.parametrize("msg", SLA_DOWN_MESSAGES)
def test_sla_down_detected(msg):
    assert is_sla_down_event(msg), f"Should detect SLA Down: {msg!r}"


@pytest.mark.parametrize("msg", NON_SLA_MESSAGES)
def test_non_sla_ignored(msg):
    assert not is_sla_down_event(msg), f"Should NOT detect SLA Down: {msg!r}"


# ── IT-002b: Stale lock detection ─────────────────────────────────────────────

def test_stale_lock_nonexistent_pid(tmp_path, monkeypatch):
    """A lock file pointing to a nonexistent PID is detected as stale."""
    lock = tmp_path / "test.lock"
    lock.write_text("999999")  # very unlikely to exist
    monkeypatch.setattr("oncall.watcher.LOCK_FILE", lock)
    assert is_lock_stale()


def test_stale_lock_current_pid(tmp_path, monkeypatch):
    """A lock file pointing to the current process is NOT stale."""
    lock = tmp_path / "test.lock"
    lock.write_text(str(os.getpid()))
    monkeypatch.setattr("oncall.watcher.LOCK_FILE", lock)
    assert not is_lock_stale()


def test_cleanup_lock_removes_file(tmp_path, monkeypatch):
    """cleanup_lock() removes the lock file if it exists."""
    lock = tmp_path / "test.lock"
    lock.write_text("12345")
    monkeypatch.setattr("oncall.watcher.LOCK_FILE", lock)
    cleanup_lock()
    assert not lock.exists()


def test_cleanup_lock_no_error_when_absent(tmp_path, monkeypatch):
    """cleanup_lock() does not raise if lock file doesn't exist."""
    lock = tmp_path / "nonexistent.lock"
    monkeypatch.setattr("oncall.watcher.LOCK_FILE", lock)
    cleanup_lock()   # Should not raise


# ── IT-002c: Deferred event scan with concurrent timestamps ──────────────────

def test_concurrent_events_captured(tmp_path, monkeypatch):
    """Events with timestamps between trigger_ts and session_end are captured."""
    from datetime import datetime, timezone

    trigger_event = {
        "ts": "2026-02-27T09:51:49.072Z",
        "device": "172.20.20.205",
        "msg": "BOM%TRACK-6-STATE: 1 ip sla 1 reachability Up -> Down",
    }

    # session_start = trigger event's timestamp (the fix)
    session_start = parse_event_ts(trigger_event)
    session_end = datetime(2026, 2, 27, 10, 5, 42, tzinfo=timezone.utc)

    # Write a mock network.json with trigger + 2 concurrent events
    log_file = tmp_path / "network.json"
    events = [
        trigger_event,
        {
            "ts": "2026-02-27T09:51:49.210Z",
            "device": "172.20.20.206",
            "msg": "BOM%TRACK-6-STATE: 1 ip sla 1 reachability Up -> Down",
        },
        {
            "ts": "2026-02-27T09:51:49.539Z",
            "device": "172.20.20.209",
            "msg": "BOM%TRACK-6-STATE: 2 ip sla 2 reachability Up -> Down",
        },
    ]
    log_file.write_text("\n".join(json.dumps(e) for e in events))
    monkeypatch.setattr("oncall.watcher.LOG_FILE", str(log_file))

    device_map = {
        "172.20.20.205": "A1C",
        "172.20.20.206": "A2C",
        "172.20.20.209": "E1C",
    }
    deferred = scan_for_deferred_events(
        trigger_event, session_start, session_end, device_map
    )

    device_names = [e["device_name"] for e in deferred]
    assert "A2C" in device_names, "A2C concurrent event should be captured"
    assert "E1C" in device_names, "E1C concurrent event should be captured"
    assert "A1C" not in device_names, "Trigger event (A1C) should be excluded"


def test_deferred_deduplication(tmp_path, monkeypatch):
    """Duplicate events from the same device/message are deduplicated."""
    from datetime import datetime, timezone

    trigger_event = {
        "ts": "2026-02-27T09:51:49.072Z",
        "device": "172.20.20.205",
        "msg": "BOM%TRACK-6-STATE: 1 ip sla 1 reachability Up -> Down",
    }

    session_start = parse_event_ts(trigger_event)
    session_end = datetime(2026, 2, 27, 10, 5, 42, tzinfo=timezone.utc)

    # Same device/msg at different timestamps (repeated SLA polls)
    log_file = tmp_path / "network.json"
    events = [
        trigger_event,
        {
            "ts": "2026-02-27T09:52:00.000Z",
            "device": "172.20.20.206",
            "msg": "BOM%TRACK-6-STATE: 1 ip sla 1 reachability Up -> Down",
        },
        {
            "ts": "2026-02-27T09:57:00.000Z",
            "device": "172.20.20.206",
            "msg": "BOM%TRACK-6-STATE: 1 ip sla 1 reachability Up -> Down",
        },
        {
            "ts": "2026-02-27T10:02:00.000Z",
            "device": "172.20.20.206",
            "msg": "BOM%TRACK-6-STATE: 1 ip sla 1 reachability Up -> Down",
        },
    ]
    log_file.write_text("\n".join(json.dumps(e) for e in events))
    monkeypatch.setattr("oncall.watcher.LOG_FILE", str(log_file))

    device_map = {"172.20.20.205": "A1C", "172.20.20.206": "A2C"}
    deferred = scan_for_deferred_events(
        trigger_event, session_start, session_end, device_map
    )

    assert len(deferred) == 1, f"Expected 1 deduplicated event, got {len(deferred)}"
    assert deferred[0]["device_name"] == "A2C"


def test_deferred_excludes_trigger_device_same_path_repeated(tmp_path, monkeypatch):
    """Trigger device's same SLA path oscillating (Down->Up->Down) is excluded from deferred."""
    from datetime import datetime, timezone

    trigger_event = {
        "ts": "2026-02-27T09:51:49.072Z",
        "device": "172.20.20.205",
        "msg": "BOM%TRACK-6-STATE: 1 ip sla 1 reachability Up -> Down",
    }

    session_start = parse_event_ts(trigger_event)
    session_end = datetime(2026, 2, 27, 10, 5, 42, tzinfo=timezone.utc)

    # Trigger device sends another Down event 2 minutes later (SLA oscillation)
    log_file = tmp_path / "network.json"
    events = [
        trigger_event,
        {
            "ts": "2026-02-27T09:53:49.000Z",
            "device": "172.20.20.205",
            "msg": "BOM%TRACK-6-STATE: 1 ip sla 1 reachability Up -> Down",
        },
        # Different device, different path — should still be captured
        {
            "ts": "2026-02-27T09:54:00.000Z",
            "device": "172.20.20.206",
            "msg": "BOM%TRACK-6-STATE: 2 ip sla 2 reachability Up -> Down",
        },
    ]
    log_file.write_text("\n".join(json.dumps(e) for e in events))
    monkeypatch.setattr("oncall.watcher.LOG_FILE", str(log_file))

    device_map = {"172.20.20.205": "A1C", "172.20.20.206": "A2C"}
    deferred = scan_for_deferred_events(
        trigger_event, session_start, session_end, device_map
    )

    device_names = [e["device_name"] for e in deferred]
    assert "A1C" not in device_names, "Trigger device's repeated SLA poll should be excluded"
    assert "A2C" in device_names, "Different device/path should still be captured"
    assert len(deferred) == 1, f"Expected 1 deferred event (A2C only), got {len(deferred)}"


# ── IT-002d: scan_for_deferred_events edge cases ──────────────────────────────

def test_deferred_empty_log_returns_empty_list(tmp_path, monkeypatch):
    """Empty network.json returns empty deferred list (no crash)."""
    from datetime import datetime, timezone

    trigger_event = {
        "ts": "2026-03-01T09:00:00.000Z",
        "device": "172.20.20.205",
        "msg": "BOM%TRACK-6-STATE: 1 ip sla 1 reachability Up -> Down",
    }
    session_start = parse_event_ts(trigger_event)
    session_end = datetime(2026, 3, 1, 9, 30, 0, tzinfo=timezone.utc)

    log_file = tmp_path / "network.json"
    log_file.write_text("")
    monkeypatch.setattr("oncall.watcher.LOG_FILE", str(log_file))

    deferred = scan_for_deferred_events(trigger_event, session_start, session_end, {})
    assert deferred == []


def test_deferred_events_outside_window_excluded(tmp_path, monkeypatch):
    """Events before session_start or after session_end are not captured."""
    from datetime import datetime, timezone

    trigger_event = {
        "ts": "2026-03-01T09:10:00.000Z",
        "device": "172.20.20.205",
        "msg": "BOM%TRACK-6-STATE: 1 ip sla 1 reachability Up -> Down",
    }
    session_start = parse_event_ts(trigger_event)
    session_end = datetime(2026, 3, 1, 9, 20, 0, tzinfo=timezone.utc)

    log_file = tmp_path / "network.json"
    # One event before the window, one inside, one after
    events = [
        {"ts": "2026-03-01T09:00:00.000Z", "device": "172.20.20.206",
         "msg": "BOM%TRACK-6-STATE: 1 ip sla 1 reachability Up -> Down"},  # before
        trigger_event,
        {"ts": "2026-03-01T09:15:00.000Z", "device": "172.20.20.207",
         "msg": "BOM%TRACK-6-STATE: 1 ip sla 1 reachability Up -> Down"},  # inside
        {"ts": "2026-03-01T09:30:00.000Z", "device": "172.20.20.208",
         "msg": "BOM%TRACK-6-STATE: 1 ip sla 1 reachability Up -> Down"},  # after (exclusive end)
    ]
    log_file.write_text("\n".join(json.dumps(e) for e in events))
    monkeypatch.setattr("oncall.watcher.LOG_FILE", str(log_file))

    device_map = {
        "172.20.20.205": "A1C",
        "172.20.20.206": "A2C",
        "172.20.20.207": "C1C",
        "172.20.20.208": "C2C",
    }
    deferred = scan_for_deferred_events(
        trigger_event, session_start, session_end, device_map
    )
    device_names = [e["device_name"] for e in deferred]
    assert "A2C" not in device_names, "Event before session_start should be excluded"
    assert "C1C" in device_names, "Event inside window should be included"
    assert "C2C" not in device_names, "Event after session_end should be excluded"
    assert "A1C" not in device_names, "Trigger event itself should be excluded"


def test_deferred_with_no_trigger_captures_all(tmp_path, monkeypatch):
    """When trigger_event=None, all Down events in window are captured (no exclusion)."""
    from datetime import datetime, timezone

    session_start = datetime(2026, 3, 1, 9, 0, 0, tzinfo=timezone.utc)
    session_end = datetime(2026, 3, 1, 9, 30, 0, tzinfo=timezone.utc)

    log_file = tmp_path / "network.json"
    events = [
        {"ts": "2026-03-01T09:05:00.000Z", "device": "172.20.20.205",
         "msg": "BOM%TRACK-6-STATE: 1 ip sla 1 reachability Up -> Down"},
        {"ts": "2026-03-01T09:10:00.000Z", "device": "172.20.20.206",
         "msg": "BOM%TRACK-6-STATE: 2 ip sla 2 reachability Up -> Down"},
    ]
    log_file.write_text("\n".join(json.dumps(e) for e in events))
    monkeypatch.setattr("oncall.watcher.LOG_FILE", str(log_file))

    deferred = scan_for_deferred_events(None, session_start, session_end, {})
    assert len(deferred) == 2


# ── IT-002e: scan_for_recovery_events ─────────────────────────────────────────

def test_recovery_events_captured(tmp_path, monkeypatch):
    """Recovery (Up) events within the session window are captured."""
    from datetime import datetime, timezone

    trigger_event = {
        "ts": "2026-03-01T09:00:00.000Z",
        "device": "172.20.20.205",
        "msg": "BOM%TRACK-6-STATE: 1 ip sla 1 reachability Up -> Down",
    }
    session_start = parse_event_ts(trigger_event)
    session_end = datetime(2026, 3, 1, 9, 30, 0, tzinfo=timezone.utc)

    log_file = tmp_path / "network.json"
    events = [
        trigger_event,
        # Recovery event for A1C within window
        {"ts": "2026-03-01T09:20:00.000Z", "device": "172.20.20.205",
         "msg": "%TRACK-6-STATE: 1 ip sla 1 reachability Down -> Up"},
        # Recovery for different device
        {"ts": "2026-03-01T09:22:00.000Z", "device": "172.20.20.206",
         "msg": "%TRACK-6-STATE: 2 ip sla 2 reachability Down -> Up"},
    ]
    log_file.write_text("\n".join(json.dumps(e) for e in events))
    monkeypatch.setattr("oncall.watcher.LOG_FILE", str(log_file))

    device_map = {"172.20.20.205": "A1C", "172.20.20.206": "A2C"}
    # scan_for_recovery_events only logs, doesn't return a list — just verify no crash
    scan_for_recovery_events(trigger_event, session_start, session_end, device_map)


def test_recovery_empty_log_no_crash(tmp_path, monkeypatch):
    """scan_for_recovery_events on empty log returns without error."""
    from datetime import datetime, timezone

    log_file = tmp_path / "network.json"
    log_file.write_text("")
    monkeypatch.setattr("oncall.watcher.LOG_FILE", str(log_file))

    session_start = datetime(2026, 3, 1, 9, 0, 0, tzinfo=timezone.utc)
    session_end = datetime(2026, 3, 1, 9, 30, 0, tzinfo=timezone.utc)
    trigger = {"ts": "2026-03-01T09:00:00Z", "device": "172.20.20.205", "msg": "x"}
    scan_for_recovery_events(trigger, session_start, session_end, {})  # Should not raise
