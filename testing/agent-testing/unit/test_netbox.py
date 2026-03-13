"""UT-020: core/netbox.py — NetBox device inventory loading.

Tests:
  - load_devices returns None when NETBOX_URL or NETBOX_TOKEN is missing
  - load_devices returns None when pynetbox raises an exception
  - load_devices returns None when NetBox returns no devices
  - load_devices correctly maps NetBox device objects to the expected schema
  - load_devices skips devices with missing primary_ip
  - load_devices skips devices with missing required custom fields
  - load_devices returns None when all devices are skipped (no valid entries)
  - Schema output matches the NETWORK.json format
"""
import os
from unittest.mock import MagicMock, patch

import pytest

import core.netbox as netbox_mod


def _make_device(name, ip, platform_slug, transport, cli_style, site_name):
    dev = MagicMock()
    dev.name = name
    dev.primary_ip = MagicMock()
    dev.primary_ip.address = f"{ip}/24"
    dev.platform = MagicMock()
    dev.platform.slug = platform_slug
    dev.custom_fields = {"transport": transport, "cli_style": cli_style}
    dev.site = MagicMock()
    dev.site.name = site_name
    return dev


SAMPLE_DEVICES = [
    _make_device("A1C", "172.20.20.205", "cisco_iosxe", "asyncssh", "ios", "Access"),
    _make_device("C1C", "172.20.20.207", "cisco_iosxe", "restconf", "ios", "Core"),
]

EXPECTED_SCHEMA = {
    "A1C": {"host": "172.20.20.205", "platform": "cisco_iosxe", "transport": "asyncssh", "cli_style": "ios", "location": "Access"},
    "C1C": {"host": "172.20.20.207", "platform": "cisco_iosxe", "transport": "restconf", "cli_style": "ios", "location": "Core"},
}


class TestNotConfigured:
    def test_returns_none_when_url_missing(self, monkeypatch):
        monkeypatch.delenv("NETBOX_URL", raising=False)
        monkeypatch.setenv("NETBOX_TOKEN", "tok")
        assert netbox_mod.load_devices() is None

    def test_returns_none_when_token_missing(self, monkeypatch):
        monkeypatch.setenv("NETBOX_URL", "http://localhost:8000")
        monkeypatch.delenv("NETBOX_TOKEN", raising=False)
        assert netbox_mod.load_devices() is None


class TestConnectionError:
    def test_returns_none_on_pynetbox_exception(self, monkeypatch):
        monkeypatch.setenv("NETBOX_URL", "http://localhost:8000")
        monkeypatch.setenv("NETBOX_TOKEN", "tok")
        with patch("pynetbox.api", side_effect=Exception("connection refused")):
            assert netbox_mod.load_devices() is None


class TestEmptyInventory:
    def test_returns_none_when_no_devices(self, monkeypatch):
        monkeypatch.setenv("NETBOX_URL", "http://localhost:8000")
        monkeypatch.setenv("NETBOX_TOKEN", "tok")
        nb = MagicMock()
        nb.dcim.devices.all.return_value = []
        with patch("pynetbox.api", return_value=nb):
            assert netbox_mod.load_devices() is None


class TestDeviceMapping:
    def _run(self, monkeypatch, devices):
        monkeypatch.setenv("NETBOX_URL", "http://localhost:8000")
        monkeypatch.setenv("NETBOX_TOKEN", "tok")
        nb = MagicMock()
        nb.dcim.devices.all.return_value = devices
        with patch("pynetbox.api", return_value=nb):
            return netbox_mod.load_devices()

    def test_correct_schema_output(self, monkeypatch):
        result = self._run(monkeypatch, SAMPLE_DEVICES)
        assert result == EXPECTED_SCHEMA

    def test_host_strips_cidr_mask(self, monkeypatch):
        result = self._run(monkeypatch, SAMPLE_DEVICES)
        assert result["A1C"]["host"] == "172.20.20.205"
        assert "/" not in result["A1C"]["host"]

    def test_skips_device_with_no_primary_ip(self, monkeypatch):
        dev = _make_device("BAD", "10.0.0.1", "cisco_iosxe", "asyncssh", "ios", "Access")
        dev.primary_ip = None
        result = self._run(monkeypatch, [dev] + SAMPLE_DEVICES)
        assert "BAD" not in result
        assert len(result) == 2

    def test_skips_device_with_missing_custom_fields(self, monkeypatch):
        dev = _make_device("BAD2", "10.0.0.2", "cisco_iosxe", "", "ios", "Access")
        result = self._run(monkeypatch, [dev] + SAMPLE_DEVICES)
        assert "BAD2" not in result

    def test_returns_none_when_all_devices_invalid(self, monkeypatch):
        dev = _make_device("BAD3", "10.0.0.3", "cisco_iosxe", "asyncssh", "ios", "Access")
        dev.primary_ip = None
        result = self._run(monkeypatch, [dev])
        assert result is None
