"""UT-019: core/vault.py — Vault secret loading with env var fallback.

Tests:
  - get_secret returns env var when Vault not configured (no VAULT_ADDR)
  - get_secret reads from Vault KV v2 when configured
  - get_secret caches path on first call (no second hvac.Client call)
  - get_secret falls back to env var on Vault connection error
  - get_secret returns None when neither Vault nor env var is set
  - Multiple keys from the same path use the cache (single Vault fetch)
"""
import importlib
import os
from unittest.mock import MagicMock, patch


def _fresh_vault():
    """Import vault with a clean module-level cache."""
    import core.vault as v
    v._cache.clear()
    return v


class TestVaultNotConfigured:
    """When VAULT_ADDR or VAULT_TOKEN is absent, fall back to env var."""

    def test_returns_env_var_when_vault_addr_missing(self, monkeypatch):
        monkeypatch.delenv("VAULT_ADDR", raising=False)
        monkeypatch.setenv("VAULT_TOKEN", "tok")
        monkeypatch.setenv("ROUTER_USERNAME", "admin")
        v = _fresh_vault()
        assert v.get_secret("ainoc/router", "username", fallback_env="ROUTER_USERNAME") == "admin"

    def test_returns_env_var_when_vault_token_missing(self, monkeypatch):
        monkeypatch.setenv("VAULT_ADDR", "http://127.0.0.1:8200")
        monkeypatch.delenv("VAULT_TOKEN", raising=False)
        monkeypatch.setenv("ROUTER_PASSWORD", "secret")
        v = _fresh_vault()
        assert v.get_secret("ainoc/router", "password", fallback_env="ROUTER_PASSWORD") == "secret"

    def test_returns_none_when_no_fallback_and_no_vault(self, monkeypatch):
        monkeypatch.delenv("VAULT_ADDR", raising=False)
        monkeypatch.delenv("VAULT_TOKEN", raising=False)
        v = _fresh_vault()
        assert v.get_secret("ainoc/router", "username") is None


class TestVaultConfigured:
    """When Vault is configured and reachable, read from KV v2."""

    def _mock_client(self, data: dict):
        client = MagicMock()
        client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": data}
        }
        return client

    def test_reads_secret_from_vault(self, monkeypatch):
        monkeypatch.setenv("VAULT_ADDR", "http://127.0.0.1:8200")
        monkeypatch.setenv("VAULT_TOKEN", "dev-root-token")
        mock_client = self._mock_client({"username": "admin", "password": "secret"})
        v = _fresh_vault()
        with patch("hvac.Client", return_value=mock_client):
            result = v.get_secret("ainoc/router", "username", fallback_env="ROUTER_USERNAME")
        assert result == "admin"

    def test_caches_path_on_first_call(self, monkeypatch):
        monkeypatch.setenv("VAULT_ADDR", "http://127.0.0.1:8200")
        monkeypatch.setenv("VAULT_TOKEN", "dev-root-token")
        mock_client = self._mock_client({"username": "admin", "password": "secret"})
        v = _fresh_vault()
        with patch("hvac.Client", return_value=mock_client) as mock_cls:
            v.get_secret("ainoc/router", "username")
            v.get_secret("ainoc/router", "password")
        # hvac.Client should only be instantiated once (second call hits cache)
        assert mock_cls.call_count == 1
        assert mock_client.secrets.kv.v2.read_secret_version.call_count == 1

    def test_multiple_paths_each_fetched_once(self, monkeypatch):
        monkeypatch.setenv("VAULT_ADDR", "http://127.0.0.1:8200")
        monkeypatch.setenv("VAULT_TOKEN", "dev-root-token")
        mock_client = self._mock_client({"api_token": "tok"})
        v = _fresh_vault()
        with patch("hvac.Client", return_value=mock_client) as mock_cls:
            v.get_secret("ainoc/jira", "api_token")
            v.get_secret("ainoc/jira", "api_token")  # second call — from cache
        assert mock_cls.call_count == 1


class TestVaultError:
    """When Vault is configured but unreachable, fall back to env var."""

    def test_falls_back_to_env_on_connection_error(self, monkeypatch):
        monkeypatch.setenv("VAULT_ADDR", "http://127.0.0.1:8200")
        monkeypatch.setenv("VAULT_TOKEN", "dev-root-token")
        monkeypatch.setenv("ROUTER_USERNAME", "fallback_user")
        v = _fresh_vault()
        with patch("hvac.Client", side_effect=Exception("connection refused")):
            result = v.get_secret("ainoc/router", "username", fallback_env="ROUTER_USERNAME")
        assert result == "fallback_user"

    def test_returns_none_when_error_and_no_fallback(self, monkeypatch):
        monkeypatch.setenv("VAULT_ADDR", "http://127.0.0.1:8200")
        monkeypatch.setenv("VAULT_TOKEN", "dev-root-token")
        v = _fresh_vault()
        with patch("hvac.Client", side_effect=Exception("connection refused")):
            result = v.get_secret("ainoc/router", "username")
        assert result is None

    def test_error_path_cached_avoids_repeated_attempts(self, monkeypatch):
        monkeypatch.setenv("VAULT_ADDR", "http://127.0.0.1:8200")
        monkeypatch.setenv("VAULT_TOKEN", "dev-root-token")
        v = _fresh_vault()
        with patch("hvac.Client", side_effect=Exception("down")) as mock_cls:
            v.get_secret("ainoc/router", "username")
            v.get_secret("ainoc/router", "password")  # second call — from cache (empty dict)
        assert mock_cls.call_count == 1
