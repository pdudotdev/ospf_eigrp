"""Unit tests for the bounded LRU cache (core/cache.py)."""
import time
from unittest.mock import patch

import pytest

from core import cache
from core.cache import cache_get, cache_set, MAX_CACHE_SIZE, CMD_TTL


def _clear():
    """Empty the module-level cache between tests."""
    cache._CACHE.clear()


# ── Basic round-trip ───────────────────────────────────────────────────────────

def test_cache_set_and_get():
    """A result stored with cache_set must be retrievable with cache_get before TTL expires.
    Basic round-trip validates the cache stores and returns values correctly.
    """
    _clear()
    result = {"device": "R1A", "parsed": {"neighbors": []}}
    cache_set("R1A", "show ip ospf neighbor", result)
    hit = cache_get("R1A", "show ip ospf neighbor", ttl=CMD_TTL)
    assert hit == result


def test_cache_miss_unknown_key():
    """cache_get must return None for a key that was never set.
    Callers treat None as a cache miss and fetch from the device.
    """
    _clear()
    assert cache_get("R99", "show ip route", ttl=CMD_TTL) is None


def test_cache_key_normalisation():
    """Command string is stripped and lowercased for the cache key."""
    _clear()
    result = {"raw": "ok"}
    cache_set("R1A", "  SHOW IP OSPF  ", result)
    assert cache_get("R1A", "show ip ospf", ttl=CMD_TTL) == result


# ── TTL expiry ─────────────────────────────────────────────────────────────────

def test_cache_miss_after_ttl_expires():
    _clear()
    result = {"raw": "data"}
    with patch("core.cache.time") as mock_time:
        mock_time.time.return_value = 1000.0
        cache_set("R1A", "show version", result)

        # Still within TTL
        mock_time.time.return_value = 1004.9
        assert cache_get("R1A", "show version", ttl=5) == result

        # Just past TTL
        mock_time.time.return_value = 1005.1
        assert cache_get("R1A", "show version", ttl=5) is None


def test_expired_entry_deleted_on_get():
    """Expired entries must be removed from the cache on access."""
    _clear()
    result = {"raw": "stale"}
    with patch("core.cache.time") as mock_time:
        mock_time.time.return_value = 1000.0
        cache_set("R2C", "show ip bgp summary", result)

        mock_time.time.return_value = 1010.0  # well past TTL
        cache_get("R2C", "show ip bgp summary", ttl=5)

    assert ("r2c", "show ip bgp summary") not in cache._CACHE


# ── Bounded eviction ──────────────────────────────────────────────────────────

def test_cache_bounded_at_max_size():
    """Inserting more than MAX_CACHE_SIZE entries must not grow the cache beyond the limit.
    An unbounded cache would cause memory growth during long troubleshooting sessions.
    """
    _clear()
    # Insert MAX_CACHE_SIZE + 50 unique entries
    for i in range(MAX_CACHE_SIZE + 50):
        cache_set(f"DEV{i}", "show version", {"index": i})
    assert len(cache._CACHE) <= MAX_CACHE_SIZE


def test_cache_evicts_oldest_first():
    """The first entry inserted should be evicted when capacity is exceeded."""
    _clear()
    cache_set("OLDEST", "show version", {"tag": "oldest"})
    for i in range(MAX_CACHE_SIZE):
        cache_set(f"DEV{i}", "show version", {"index": i})
    # "OLDEST" should have been evicted
    assert ("oldest", "show version") not in cache._CACHE


def test_update_existing_key_does_not_evict():
    """Updating an existing key must not count as a new entry for eviction."""
    _clear()
    # Fill to capacity
    for i in range(MAX_CACHE_SIZE):
        cache_set(f"DEV{i}", "show version", {"index": i})
    size_before = len(cache._CACHE)
    # Update an existing key — should NOT trigger eviction
    cache_set("DEV0", "show version", {"index": 999})
    assert len(cache._CACHE) == size_before
