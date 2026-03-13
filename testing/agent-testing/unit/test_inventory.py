"""UT-024 — Inventory loader unit tests.

Tests for core/inventory.py: _load_json_fallback() and the NetBox-vs-JSON
fallback decision at module level.

Two testing strategies are used:
- _load_json_fallback() is tested DIRECTLY by patching _INVENTORY_FILE on the
  already-loaded module object (no reload needed for file-path logic).
- The NetBox-vs-fallback MODULE-LEVEL DECISION is tested via importlib.reload():
  when load_devices() is patched to return None, the reload verifies that
  _load_json_fallback() is called and devices is populated from NETWORK.json.

Validates:
- _load_json_fallback loads correct dict from a valid JSON file
- _load_json_fallback raises RuntimeError when the file is missing
- _load_json_fallback handles an empty JSON object (returns {})
- NetBox returns devices → module-level `devices` equals the NetBox result
- NetBox returns None → module-level `devices` is populated from NETWORK.json
"""
import importlib
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import core.inventory as inv_mod


class TestLoadJsonFallback:
    def test_loads_correct_dict_from_json_file(self, tmp_path):
        """_load_json_fallback reads devices dict from NETWORK.json."""
        json_devices = {
            "C1C": {"host": "172.20.20.207", "platform": "cisco_iosxe",
                    "transport": "restconf", "cli_style": "ios"},
        }
        json_file = tmp_path / "NETWORK.json"
        json_file.write_text(json.dumps(json_devices))

        with patch.object(inv_mod, "_INVENTORY_FILE", str(json_file)):
            result = inv_mod._load_json_fallback()
        assert result == json_devices

    def test_missing_file_raises_runtime_error(self, tmp_path):
        """_load_json_fallback raises RuntimeError when NETWORK.json is absent."""
        missing = tmp_path / "nonexistent.json"
        with patch.object(inv_mod, "_INVENTORY_FILE", str(missing)):
            with pytest.raises(RuntimeError, match="Inventory file not found"):
                inv_mod._load_json_fallback()

    def test_empty_json_object_returns_empty_dict(self, tmp_path):
        """Empty JSON object yields empty devices dict (no crash)."""
        json_file = tmp_path / "NETWORK.json"
        json_file.write_text("{}")
        with patch.object(inv_mod, "_INVENTORY_FILE", str(json_file)):
            result = inv_mod._load_json_fallback()
        assert result == {}


class TestInventoryFallbackDecision:
    def test_netbox_result_used_when_available(self):
        """When NetBox returns devices, module-level `devices` uses them directly."""
        netbox_devices = {
            "A1C": {"host": "172.20.20.205", "platform": "cisco_iosxe",
                    "transport": "asyncssh", "cli_style": "ios"},
        }
        with patch("core.netbox.load_devices", return_value=netbox_devices):
            importlib.reload(inv_mod)
        assert inv_mod.devices == netbox_devices

    def test_json_fallback_when_netbox_returns_none(self):
        """When NetBox returns None, devices is populated from NETWORK.json (real file).

        Uses the actual NETWORK.json (the real project inventory) so that the
        reload picks up the correct path set at module init. Verifies that
        devices is a non-empty dict with the expected device schema.
        """
        with patch("core.netbox.load_devices", return_value=None):
            importlib.reload(inv_mod)
        # Verify that devices came from JSON, not None
        assert isinstance(inv_mod.devices, dict)
        assert len(inv_mod.devices) > 0
        # Each entry must have the basic required fields
        for name, dev in inv_mod.devices.items():
            assert "host" in dev, f"Device {name} missing 'host'"
            assert "transport" in dev, f"Device {name} missing 'transport'"
            assert "cli_style" in dev, f"Device {name} missing 'cli_style'"
