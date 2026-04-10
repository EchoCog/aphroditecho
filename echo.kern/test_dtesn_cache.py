#!/usr/bin/env python3
"""
Comprehensive tests for the DTESN Server-Side Caching Layer.

Tests cover:
- Cache key generation determinism and collision resistance
- L1 in-memory cache: LRU eviction, TTL expiry, thread safety
- L2 Redis cache: graceful degradation when unavailable
- DTESNCache multi-level lookup and promotion
- CachedDTESNSystem wrapper: hit/miss, config invalidation
- Cache statistics accuracy
- Serialization round-trips for numpy arrays
- Performance validation (50%+ improvement target)
"""

import sys
import os
import time
import threading
import unittest
from unittest.mock import MagicMock
from typing import Dict, Any, List, Tuple

import numpy as np

# Ensure echo.kern is importable
sys.path.insert(0, os.path.dirname(__file__))

from dtesn_cache import (  # noqa: E402
    CacheConfig,
    CacheEntry,
    CacheEntryType,
    CacheStatistics,
    CachedDTESNSystem,
    DTESNCache,
    L1MemoryCache,
    L2RedisCache,
    _deserialize_from_redis,
    _estimate_size,
    _serialize_for_redis,
    compute_config_fingerprint,
    generate_cache_key,
)


class TestCacheKeyGeneration(unittest.TestCase):
    """Tests for deterministic cache key generation."""

    def test_same_inputs_produce_same_key(self):
        arr = np.array([1.0, 2.0, 3.0])
        key1 = generate_cache_key(CacheEntryType.SYSTEM_UPDATE, arr, "fp1")
        key2 = generate_cache_key(CacheEntryType.SYSTEM_UPDATE, arr, "fp1")
        self.assertEqual(key1, key2)

    def test_different_inputs_produce_different_keys(self):
        arr1 = np.array([1.0, 2.0, 3.0])
        arr2 = np.array([1.0, 2.0, 4.0])
        key1 = generate_cache_key(CacheEntryType.SYSTEM_UPDATE, arr1, "fp1")
        key2 = generate_cache_key(CacheEntryType.SYSTEM_UPDATE, arr2, "fp1")
        self.assertNotEqual(key1, key2)

    def test_different_types_produce_different_keys(self):
        arr = np.array([1.0, 2.0, 3.0])
        key1 = generate_cache_key(CacheEntryType.SYSTEM_UPDATE, arr, "fp1")
        key2 = generate_cache_key(CacheEntryType.SYSTEM_SUMMARY, arr, "fp1")
        self.assertNotEqual(key1, key2)

    def test_different_config_produces_different_keys(self):
        arr = np.array([1.0, 2.0, 3.0])
        key1 = generate_cache_key(CacheEntryType.SYSTEM_UPDATE, arr, "fp1")
        key2 = generate_cache_key(CacheEntryType.SYSTEM_UPDATE, arr, "fp2")
        self.assertNotEqual(key1, key2)

    def test_dict_input_deterministic(self):
        d = {"b": 2, "a": 1}
        key1 = generate_cache_key(CacheEntryType.SYSTEM_UPDATE, d, "fp")
        key2 = generate_cache_key(CacheEntryType.SYSTEM_UPDATE, d, "fp")
        self.assertEqual(key1, key2)

    def test_extra_parts_affect_key(self):
        key1 = generate_cache_key(
            CacheEntryType.SYSTEM_UPDATE, None, "fp", ["part1"]
        )
        key2 = generate_cache_key(
            CacheEntryType.SYSTEM_UPDATE, None, "fp", ["part2"]
        )
        self.assertNotEqual(key1, key2)

    def test_none_input_produces_valid_key(self):
        key = generate_cache_key(CacheEntryType.SYSTEM_UPDATE, None, "")
        self.assertIsInstance(key, str)
        self.assertEqual(len(key), 64)  # SHA-256 hex digest


class TestConfigFingerprint(unittest.TestCase):
    """Tests for configuration fingerprinting."""

    def test_same_config_same_fingerprint(self):
        cfg = {"reservoir_size": 100, "spectral_radius": 0.95}
        fp1 = compute_config_fingerprint(cfg)
        fp2 = compute_config_fingerprint(cfg)
        self.assertEqual(fp1, fp2)

    def test_different_config_different_fingerprint(self):
        cfg1 = {"reservoir_size": 100}
        cfg2 = {"reservoir_size": 200}
        fp1 = compute_config_fingerprint(cfg1)
        fp2 = compute_config_fingerprint(cfg2)
        self.assertNotEqual(fp1, fp2)

    def test_dataclass_fingerprint(self):
        from dataclasses import dataclass

        @dataclass
        class MockConfig:
            size: int = 100
            radius: float = 0.95

        cfg = MockConfig()
        fp = compute_config_fingerprint(cfg)
        self.assertIsInstance(fp, str)
        self.assertEqual(len(fp), 16)  # Truncated to 16 chars


class TestSizeEstimation(unittest.TestCase):
    """Tests for value size estimation."""

    def test_numpy_array_size(self):
        arr = np.zeros(100, dtype=np.float32)
        size = _estimate_size(arr)
        self.assertEqual(size, arr.nbytes)

    def test_dict_size(self):
        d = {"key": "value"}
        size = _estimate_size(d)
        self.assertGreater(size, 0)

    def test_string_size(self):
        s = "hello world"
        size = _estimate_size(s)
        self.assertEqual(size, len(s.encode("utf-8")))

    def test_nested_dict_size(self):
        d = {"arr": np.zeros(10), "nested": {"x": 42}}
        size = _estimate_size(d)
        self.assertGreater(size, np.zeros(10).nbytes)


class TestSerialization(unittest.TestCase):
    """Tests for Redis serialization round-trips."""

    def test_numpy_array_roundtrip(self):
        arr = np.array([1.0, 2.0, 3.0], dtype=np.float64)
        raw = _serialize_for_redis(arr)
        result = _deserialize_from_redis(raw)
        np.testing.assert_array_almost_equal(result, arr)

    def test_dict_with_numpy_roundtrip(self):
        data = {
            "state": np.array([1.0, 2.0]),
            "mode": "full_dtesn",
            "count": 42,
        }
        raw = _serialize_for_redis(data)
        result = _deserialize_from_redis(raw)
        np.testing.assert_array_almost_equal(result["state"], data["state"])
        self.assertEqual(result["mode"], "full_dtesn")
        self.assertEqual(result["count"], 42)

    def test_nested_structure_roundtrip(self):
        data = {
            "reservoir_states": {
                "r0": np.array([0.1, 0.2]),
                "r1": np.array([0.3, 0.4]),
            },
            "metadata": {"oeis_compliant": True},
        }
        raw = _serialize_for_redis(data)
        result = _deserialize_from_redis(raw)
        np.testing.assert_array_almost_equal(
            result["reservoir_states"]["r0"], [0.1, 0.2]
        )
        self.assertTrue(result["metadata"]["oeis_compliant"])

    def test_plain_dict_roundtrip(self):
        data = {"a": 1, "b": "hello", "c": [1, 2, 3]}
        raw = _serialize_for_redis(data)
        result = _deserialize_from_redis(raw)
        self.assertEqual(result, data)


class TestL1MemoryCache(unittest.TestCase):
    """Tests for the in-memory LRU cache."""

    def _make_entry(
        self, key: str, value: Any = "test", size: int = 100, ttl: float = 60.0
    ) -> CacheEntry:
        return CacheEntry(
            key=key,
            value=value,
            entry_type=CacheEntryType.SYSTEM_UPDATE,
            created_at=time.monotonic(),
            ttl_seconds=ttl,
            size_bytes=size,
        )

    def test_put_and_get(self):
        cache = L1MemoryCache(max_entries=10)
        entry = self._make_entry("k1", "v1")
        cache.put(entry)
        result = cache.get("k1")
        self.assertIsNotNone(result)
        self.assertEqual(result.value, "v1")

    def test_miss_returns_none(self):
        cache = L1MemoryCache(max_entries=10)
        self.assertIsNone(cache.get("nonexistent"))

    def test_lru_eviction(self):
        cache = L1MemoryCache(max_entries=3)
        cache.put(self._make_entry("k1", "v1"))
        cache.put(self._make_entry("k2", "v2"))
        cache.put(self._make_entry("k3", "v3"))

        # Access k1 to make it recently used
        cache.get("k1")

        # Adding k4 should evict k2 (LRU)
        cache.put(self._make_entry("k4", "v4"))
        self.assertIsNone(cache.get("k2"))
        self.assertIsNotNone(cache.get("k1"))
        self.assertIsNotNone(cache.get("k4"))

    def test_ttl_expiry(self):
        cache = L1MemoryCache(max_entries=10)
        # Create entry with very short TTL
        entry = CacheEntry(
            key="k1",
            value="v1",
            entry_type=CacheEntryType.SYSTEM_UPDATE,
            created_at=time.monotonic() - 10,  # Created 10s ago
            ttl_seconds=1.0,  # TTL of 1s
            size_bytes=100,
        )
        cache.put(entry)
        # Should be expired
        result = cache.get("k1")
        self.assertIsNone(result)

    def test_memory_limit_eviction(self):
        # 500 bytes max
        mb = 500 / (1024 * 1024)
        cache = L1MemoryCache(max_entries=100, max_memory_mb=mb)
        cache.put(self._make_entry("k1", "v1", size=200))
        cache.put(self._make_entry("k2", "v2", size=200))
        # Adding a 200-byte entry should evict k1 to stay under 500 bytes
        cache.put(self._make_entry("k3", "v3", size=200))
        self.assertIsNone(cache.get("k1"))
        self.assertIsNotNone(cache.get("k2"))
        self.assertIsNotNone(cache.get("k3"))

    def test_invalidate_single(self):
        cache = L1MemoryCache(max_entries=10)
        cache.put(self._make_entry("k1"))
        self.assertTrue(cache.invalidate("k1"))
        self.assertIsNone(cache.get("k1"))
        self.assertFalse(cache.invalidate("k1"))

    def test_invalidate_by_type(self):
        cache = L1MemoryCache(max_entries=10)
        e1 = self._make_entry("k1")
        e1.entry_type = CacheEntryType.SYSTEM_UPDATE
        e2 = self._make_entry("k2")
        e2.entry_type = CacheEntryType.SYSTEM_SUMMARY
        cache.put(e1)
        cache.put(e2)

        count = cache.invalidate_by_type(CacheEntryType.SYSTEM_UPDATE)
        self.assertEqual(count, 1)
        self.assertIsNone(cache.get("k1"))
        self.assertIsNotNone(cache.get("k2"))

    def test_invalidate_by_config(self):
        cache = L1MemoryCache(max_entries=10)
        e1 = self._make_entry("k1")
        e1.config_fingerprint = "old_fp"
        e2 = self._make_entry("k2")
        e2.config_fingerprint = "new_fp"
        cache.put(e1)
        cache.put(e2)

        count = cache.invalidate_by_config("new_fp")
        self.assertEqual(count, 1)
        self.assertIsNone(cache.get("k1"))
        self.assertIsNotNone(cache.get("k2"))

    def test_clear(self):
        cache = L1MemoryCache(max_entries=10)
        cache.put(self._make_entry("k1"))
        cache.put(self._make_entry("k2"))
        count = cache.clear()
        self.assertEqual(count, 2)
        self.assertEqual(cache.size, 0)

    def test_size_and_memory(self):
        cache = L1MemoryCache(max_entries=10)
        cache.put(self._make_entry("k1", size=100))
        cache.put(self._make_entry("k2", size=200))
        self.assertEqual(cache.size, 2)
        self.assertEqual(cache.memory_bytes, 300)

    def test_update_existing_key(self):
        cache = L1MemoryCache(max_entries=10)
        cache.put(self._make_entry("k1", "v1", size=100))
        cache.put(self._make_entry("k1", "v2", size=150))
        self.assertEqual(cache.size, 1)
        self.assertEqual(cache.memory_bytes, 150)
        self.assertEqual(cache.get("k1").value, "v2")

    def test_hit_count_increments(self):
        cache = L1MemoryCache(max_entries=10)
        cache.put(self._make_entry("k1", "v1"))
        cache.get("k1")
        cache.get("k1")
        entry = cache.get("k1")
        self.assertEqual(entry.hit_count, 3)

    def test_thread_safety(self):
        cache = L1MemoryCache(max_entries=100)
        errors = []

        def writer(start: int):
            try:
                for i in range(50):
                    cache.put(self._make_entry(f"w{start}_{i}", f"v{i}"))
            except Exception as e:
                errors.append(e)

        def reader(start: int):
            try:
                for i in range(50):
                    cache.get(f"w{start}_{i}")
            except Exception as e:
                errors.append(e)

        threads = []
        for t in range(4):
            threads.append(threading.Thread(target=writer, args=(t,)))
            threads.append(threading.Thread(target=reader, args=(t,)))

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Thread safety errors: {errors}")


class TestL2RedisCache(unittest.TestCase):
    """Tests for Redis cache graceful degradation."""

    def test_unavailable_redis_returns_none(self):
        # Redis won't be available in test environment
        cache = L2RedisCache(redis_url="redis://localhost:59999/0")
        self.assertFalse(cache.available)
        self.assertIsNone(cache.get("key"))
        self.assertFalse(cache.put("key", b"data"))
        self.assertFalse(cache.invalidate("key"))
        self.assertEqual(cache.clear(), 0)


class TestCacheStatistics(unittest.TestCase):
    """Tests for cache statistics tracking."""

    def test_initial_stats(self):
        stats = CacheStatistics()
        self.assertEqual(stats.l1_hits, 0)
        self.assertEqual(stats.l1_misses, 0)
        self.assertEqual(stats.overall_hit_rate, 0.0)

    def test_hit_rate_calculation(self):
        stats = CacheStatistics()
        stats.l1_hits = 7
        stats.l1_misses = 3
        self.assertAlmostEqual(stats.l1_hit_rate, 0.7)

    def test_overall_hit_rate(self):
        stats = CacheStatistics()
        stats.l1_hits = 5
        stats.l2_hits = 3
        stats.total_get_ops = 10
        self.assertAlmostEqual(stats.overall_hit_rate, 0.8)

    def test_to_dict(self):
        stats = CacheStatistics()
        stats.l1_hits = 10
        d = stats.to_dict()
        self.assertIn("l1_hits", d)
        self.assertIn("overall_hit_rate", d)
        self.assertEqual(d["l1_hits"], 10)

    def test_uptime_positive(self):
        stats = CacheStatistics()
        time.sleep(0.01)
        self.assertGreater(stats.uptime_seconds, 0)


class TestDTESNCache(unittest.TestCase):
    """Tests for the multi-level DTESNCache."""

    def setUp(self):
        self.config = CacheConfig(
            l1_max_entries=100,
            l1_max_memory_mb=1.0,
            default_ttl_seconds=60.0,
            enable_l2=False,
        )
        self.cache = DTESNCache(self.config)

    def test_put_and_get(self):
        arr = np.array([1.0, 2.0, 3.0])
        self.cache.put(
            CacheEntryType.SYSTEM_UPDATE,
            value={"output": arr.tolist()},
            input_data=arr,
            config_fingerprint="fp1",
        )
        result = self.cache.get(
            CacheEntryType.SYSTEM_UPDATE,
            input_data=arr,
            config_fingerprint="fp1",
        )
        self.assertIsNotNone(result)
        self.assertEqual(result["output"], [1.0, 2.0, 3.0])

    def test_miss_returns_none(self):
        result = self.cache.get(
            CacheEntryType.SYSTEM_UPDATE,
            input_data=np.array([9.9]),
            config_fingerprint="fp1",
        )
        self.assertIsNone(result)

    def test_config_fingerprint_mismatch_invalidates(self):
        arr = np.array([1.0, 2.0])
        self.cache.put(
            CacheEntryType.SYSTEM_UPDATE,
            value="result",
            input_data=arr,
            config_fingerprint="old_fp",
        )
        # Lookup with new fingerprint should miss
        result = self.cache.get(
            CacheEntryType.SYSTEM_UPDATE,
            input_data=arr,
            config_fingerprint="new_fp",
        )
        self.assertIsNone(result)

    def test_bypass_cache_types(self):
        config = CacheConfig(
            bypass_cache_types=[CacheEntryType.RESERVOIR_STATE.value]
        )
        cache = DTESNCache(config)
        cache.put(
            CacheEntryType.RESERVOIR_STATE,
            value="data",
            input_data=np.array([1.0]),
        )
        result = cache.get(
            CacheEntryType.RESERVOIR_STATE,
            input_data=np.array([1.0]),
        )
        self.assertIsNone(result)
        self.assertGreater(cache.stats.cache_bypasses, 0)

    def test_invalidate_specific(self):
        arr = np.array([1.0])
        self.cache.put(
            CacheEntryType.SYSTEM_UPDATE,
            value="data",
            input_data=arr,
            config_fingerprint="fp",
        )
        removed = self.cache.invalidate(
            CacheEntryType.SYSTEM_UPDATE,
            input_data=arr,
            config_fingerprint="fp",
        )
        self.assertTrue(removed)
        self.assertIsNone(
            self.cache.get(
                CacheEntryType.SYSTEM_UPDATE,
                input_data=arr,
                config_fingerprint="fp",
            )
        )

    def test_invalidate_by_type(self):
        self.cache.put(CacheEntryType.SYSTEM_UPDATE, value="a")
        self.cache.put(CacheEntryType.SYSTEM_SUMMARY, value="b")
        count = self.cache.invalidate_by_type(CacheEntryType.SYSTEM_UPDATE)
        self.assertEqual(count, 1)

    def test_invalidate_on_config_change(self):
        self.cache.put(
            CacheEntryType.SYSTEM_UPDATE,
            value="data",
            config_fingerprint="old_fp",
        )
        count = self.cache.invalidate_on_config_change("new_fp")
        self.assertEqual(count, 1)

    def test_clear(self):
        self.cache.put(CacheEntryType.SYSTEM_UPDATE, value="a")
        self.cache.put(CacheEntryType.SYSTEM_SUMMARY, value="b")
        count = self.cache.clear()
        self.assertEqual(count, 2)

    def test_statistics_tracking(self):
        arr = np.array([1.0])
        # One miss
        self.cache.get(CacheEntryType.SYSTEM_UPDATE, input_data=arr)
        # One put
        self.cache.put(CacheEntryType.SYSTEM_UPDATE, value="v", input_data=arr)
        # One hit
        self.cache.get(CacheEntryType.SYSTEM_UPDATE, input_data=arr)

        stats = self.cache.get_stats_dict()
        self.assertEqual(stats["total_get_ops"], 2)
        self.assertEqual(stats["total_put_ops"], 1)
        self.assertEqual(stats["l1_hits"], 1)
        self.assertEqual(stats["l1_misses"], 1)

    def test_reset_stats(self):
        self.cache.put(CacheEntryType.SYSTEM_UPDATE, value="v")
        self.cache.reset_stats()
        self.assertEqual(self.cache.stats.total_put_ops, 0)

    def test_get_stats_dict_contains_all_fields(self):
        stats = self.cache.get_stats_dict()
        expected_keys = [
            "l1_hits", "l1_misses", "l1_hit_rate",
            "l2_hits", "l2_misses", "l2_hit_rate",
            "overall_hit_rate", "evictions", "invalidations",
            "total_put_ops", "total_get_ops", "total_bytes_cached",
            "cache_bypasses", "uptime_seconds",
            "l1_entries", "l1_memory_bytes", "l2_available", "cache_version",
        ]
        for key in expected_keys:
            self.assertIn(key, stats, f"Missing stats key: {key}")


class MockDTESNSystem:
    """Mock DTESN system for testing CachedDTESNSystem."""

    def __init__(self):
        self.config = MagicMock()
        self.config.__dict__ = {"reservoir_size": 100, "spectral_radius": 0.95}
        self.update_call_count = 0
        self.summary_call_count = 0
        self.validate_call_count = 0

    def update_system(self, global_input: np.ndarray) -> Dict[str, Any]:
        self.update_call_count += 1
        return {
            "mode": "full_dtesn",
            "active_reservoirs": 17,
            "output": global_input.tolist(),
        }

    def get_system_summary(self) -> Dict[str, Any]:
        self.summary_call_count += 1
        return {
            "configuration": {"reservoir_count": 17},
            "system_metrics": {"total_updates": 42},
        }

    def validate_integration(self) -> Tuple[bool, List[str]]:
        self.validate_call_count += 1
        return True, []


class TestCachedDTESNSystem(unittest.TestCase):
    """Tests for the CachedDTESNSystem wrapper."""

    def setUp(self):
        self.mock_system = MockDTESNSystem()
        self.config = CacheConfig(
            l1_max_entries=100,
            default_ttl_seconds=60.0,
            enable_l2=False,
        )
        self.cached = CachedDTESNSystem(self.mock_system, self.config)

    def test_update_system_caches_result(self):
        arr = np.array([1.0, 2.0, 3.0])
        result1 = self.cached.update_system(arr)
        result2 = self.cached.update_system(arr)

        # Should only call underlying system once
        self.assertEqual(self.mock_system.update_call_count, 1)
        self.assertEqual(result1, result2)

    def test_update_system_different_inputs_not_cached(self):
        arr1 = np.array([1.0, 2.0])
        arr2 = np.array([3.0, 4.0])
        self.cached.update_system(arr1)
        self.cached.update_system(arr2)
        self.assertEqual(self.mock_system.update_call_count, 2)

    def test_get_system_summary_caches(self):
        result1 = self.cached.get_system_summary()
        result2 = self.cached.get_system_summary()
        self.assertEqual(self.mock_system.summary_call_count, 1)
        self.assertEqual(result1, result2)

    def test_validate_integration_caches(self):
        is_valid1, issues1 = self.cached.validate_integration()
        is_valid2, issues2 = self.cached.validate_integration()
        self.assertEqual(self.mock_system.validate_call_count, 1)
        self.assertTrue(is_valid1)
        self.assertTrue(is_valid2)

    def test_config_change_invalidates(self):
        arr = np.array([1.0, 2.0])
        self.cached.update_system(arr)

        # Change config
        self.mock_system.config.__dict__["reservoir_size"] = 200
        self.cached.on_config_change()

        # Should recompute
        self.cached.update_system(arr)
        self.assertEqual(self.mock_system.update_call_count, 2)

    def test_cache_stats_accessible(self):
        stats = self.cached.get_cache_stats()
        self.assertIsInstance(stats, dict)
        self.assertIn("l1_hits", stats)

    def test_system_property(self):
        self.assertIs(self.cached.system, self.mock_system)

    def test_cache_property(self):
        self.assertIsInstance(self.cached.cache, DTESNCache)


class TestPerformanceImprovement(unittest.TestCase):
    """Validate caching achieves 50% improvement."""

    def test_cached_response_time_improvement(self):
        """Measure that cached lookups are at least 50% faster than uncached."""
        mock_system = MockDTESNSystem()

        # Add artificial processing delay to simulate real DTESN computation
        original_update = mock_system.update_system

        def slow_update(global_input):
            time.sleep(0.005)  # 5ms simulated processing time
            return original_update(global_input)

        mock_system.update_system = slow_update

        config = CacheConfig(enable_l2=False)
        cached = CachedDTESNSystem(mock_system, config)

        arr = np.random.random(10)

        # Warm up: first call (cache miss)
        start = time.perf_counter()
        cached.update_system(arr)
        uncached_time = time.perf_counter() - start

        # Second call (cache hit)
        start = time.perf_counter()
        cached.update_system(arr)
        cached_time = time.perf_counter() - start

        # Cached should be at least 50% faster
        improvement = 1.0 - (cached_time / uncached_time)
        self.assertGreater(
            improvement,
            0.50,
            f"Cache improvement {improvement:.1%} did not meet 50% target. "
            f"Uncached: {uncached_time*1000:.2f}ms, "
            f"Cached: {cached_time*1000:.2f}ms",
        )

    def test_bulk_lookup_performance(self):
        """Test that many cached lookups are fast."""
        config = CacheConfig(l1_max_entries=1000, enable_l2=False)
        cache = DTESNCache(config)

        # Populate cache
        inputs = [np.random.random(10) for _ in range(100)]
        for inp in inputs:
            cache.put(
                CacheEntryType.SYSTEM_UPDATE,
                value={"result": inp.tolist()},
                input_data=inp,
                config_fingerprint="fp",
            )

        # Measure lookup speed
        start = time.perf_counter()
        hits = 0
        for inp in inputs:
            result = cache.get(
                CacheEntryType.SYSTEM_UPDATE,
                input_data=inp,
                config_fingerprint="fp",
            )
            if result is not None:
                hits += 1
        elapsed = time.perf_counter() - start

        self.assertEqual(hits, 100)
        # 100 lookups should complete in well under 100ms
        self.assertLess(elapsed, 0.1, f"Bulk lookups took {elapsed*1000:.1f}ms")


class TestCacheEntryExpiry(unittest.TestCase):
    """Tests for CacheEntry TTL properties."""

    def test_not_expired_within_ttl(self):
        entry = CacheEntry(
            key="k",
            value="v",
            entry_type=CacheEntryType.SYSTEM_UPDATE,
            created_at=time.monotonic(),
            ttl_seconds=60.0,
        )
        self.assertFalse(entry.is_expired)

    def test_expired_after_ttl(self):
        entry = CacheEntry(
            key="k",
            value="v",
            entry_type=CacheEntryType.SYSTEM_UPDATE,
            created_at=time.monotonic() - 120,
            ttl_seconds=60.0,
        )
        self.assertTrue(entry.is_expired)

    def test_age_seconds(self):
        entry = CacheEntry(
            key="k",
            value="v",
            entry_type=CacheEntryType.SYSTEM_UPDATE,
            created_at=time.monotonic() - 10,
            ttl_seconds=60.0,
        )
        self.assertGreaterEqual(entry.age_seconds, 9.9)


class TestCacheConfig(unittest.TestCase):
    """Tests for CacheConfig defaults and overrides."""

    def test_default_config(self):
        config = CacheConfig()
        self.assertEqual(config.l1_max_entries, 1024)
        self.assertEqual(config.default_ttl_seconds, 300.0)
        self.assertFalse(config.enable_l2)

    def test_custom_ttls(self):
        config = CacheConfig()
        self.assertIn(
            CacheEntryType.TREE_CLASSIFICATION.value,
            config.entry_ttls,
        )
        self.assertEqual(
            config.entry_ttls[CacheEntryType.TREE_CLASSIFICATION.value],
            600.0,
        )

    def test_cache_version(self):
        config = CacheConfig(cache_version="v2")
        cache = DTESNCache(config)
        # Put under v2
        cache.put(CacheEntryType.SYSTEM_UPDATE, value="data")
        # Should find it
        result = cache.get(CacheEntryType.SYSTEM_UPDATE)
        self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
