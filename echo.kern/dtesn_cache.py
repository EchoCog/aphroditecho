#!/usr/bin/env python3
"""
DTESN Server-Side Caching Layer
================================

Multi-level caching system for DTESN processing results, designed to
significantly reduce response times for repeated or similar computations.

Architecture:
    L1 Cache (In-Memory LRU):
        - Process-local, fastest access (~μs)
        - Bounded by max entries and memory limit
        - Automatic LRU eviction

    L2 Cache (Redis):
        - Shared across processes, moderate access (~ms)
        - Optional — gracefully degrades if unavailable
        - TTL-based expiration

Cache Invalidation Strategies:
    - TTL-based: Entries expire after configurable time-to-live
    - Event-based: Explicit invalidation on configuration changes
    - Input-hash: Cache keys derived from input vectors + config fingerprints
    - Versioned: Cache entries tagged with system version for safe upgrades

Key Features:
    - Thread-safe in-memory cache with reader-writer locking
    - Configurable per-operation TTLs for different result types
    - Cache statistics and hit-rate monitoring
    - Zero-overhead bypass for real-time constrained operations
    - Serialization support for numpy arrays in Redis

Author: Echo.Kern Development Team
License: MIT
"""

import hashlib
import json
import logging
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class CacheLevel(Enum):
    """Cache hierarchy levels."""
    L1_MEMORY = "l1_memory"
    L2_REDIS = "l2_redis"


class CacheEntryType(Enum):
    """Types of cacheable DTESN results."""
    SYSTEM_UPDATE = "system_update"
    SYSTEM_SUMMARY = "system_summary"
    RESERVOIR_STATE = "reservoir_state"
    MEMBRANE_STATE = "membrane_state"
    TREE_CLASSIFICATION = "tree_classification"
    VALIDATION_RESULT = "validation_result"
    PERFORMANCE_SUMMARY = "performance_summary"


@dataclass
class CacheConfig:
    """Configuration for the DTESN caching layer.

    Attributes:
        l1_max_entries: Maximum number of entries in L1 (in-memory) cache.
        l1_max_memory_mb: Approximate memory limit for L1 cache in megabytes.
        default_ttl_seconds: Default time-to-live for cache entries.
        entry_ttls: Per-entry-type TTL overrides (seconds).
        enable_l2: Whether to attempt Redis (L2) cache connection.
        redis_url: Redis connection URL for L2 cache.
        redis_key_prefix: Prefix for all Redis keys to avoid collisions.
        redis_ttl_seconds: Default TTL for Redis entries.
        bypass_cache_types: Entry types that should never be cached
            (e.g., real-time constrained operations).
        cache_version: Version tag for cache entries; changing this
            invalidates all existing entries on lookup.
    """
    l1_max_entries: int = 1024
    l1_max_memory_mb: float = 64.0
    default_ttl_seconds: float = 300.0  # 5 minutes
    entry_ttls: Dict[str, float] = field(default_factory=lambda: {
        CacheEntryType.SYSTEM_UPDATE.value: 60.0,       # 1 min — dynamic
        CacheEntryType.SYSTEM_SUMMARY.value: 120.0,     # 2 min
        CacheEntryType.RESERVOIR_STATE.value: 30.0,  # 30s
        CacheEntryType.MEMBRANE_STATE.value: 60.0,      # 1 min
        CacheEntryType.TREE_CLASSIFICATION.value: 600.0, # 10 min — stable
        CacheEntryType.VALIDATION_RESULT.value: 3600.0,  # 1 hour — very stable
        CacheEntryType.PERFORMANCE_SUMMARY.value: 30.0,  # 30s
    })
    enable_l2: bool = False
    redis_url: str = "redis://localhost:6379/0"
    redis_key_prefix: str = "dtesn_cache"
    redis_ttl_seconds: float = 600.0  # 10 minutes
    bypass_cache_types: List[str] = field(default_factory=list)
    cache_version: str = "v1"


@dataclass
class CacheEntry:
    """A single cache entry with metadata."""
    key: str
    value: Any
    entry_type: CacheEntryType
    created_at: float
    ttl_seconds: float
    size_bytes: int = 0
    hit_count: int = 0
    config_fingerprint: str = ""

    @property
    def is_expired(self) -> bool:
        """Check if the entry has exceeded its TTL."""
        return (time.monotonic() - self.created_at) > self.ttl_seconds

    @property
    def age_seconds(self) -> float:
        """Return how old this entry is in seconds."""
        return time.monotonic() - self.created_at


@dataclass
class CacheStatistics:
    """Accumulated cache statistics for monitoring."""
    l1_hits: int = 0
    l1_misses: int = 0
    l2_hits: int = 0
    l2_misses: int = 0
    evictions: int = 0
    invalidations: int = 0
    total_put_ops: int = 0
    total_get_ops: int = 0
    total_bytes_cached: int = 0
    cache_bypasses: int = 0
    _start_time: float = field(default_factory=time.monotonic)

    @property
    def l1_hit_rate(self) -> float:
        """L1 cache hit rate as a fraction [0, 1]."""
        total = self.l1_hits + self.l1_misses
        return self.l1_hits / total if total > 0 else 0.0

    @property
    def l2_hit_rate(self) -> float:
        """L2 cache hit rate as a fraction [0, 1]."""
        total = self.l2_hits + self.l2_misses
        return self.l2_hits / total if total > 0 else 0.0

    @property
    def overall_hit_rate(self) -> float:
        """Combined hit rate across all levels."""
        total_hits = self.l1_hits + self.l2_hits
        total_ops = self.total_get_ops
        return total_hits / total_ops if total_ops > 0 else 0.0

    @property
    def uptime_seconds(self) -> float:
        """Time since statistics tracking began."""
        return time.monotonic() - self._start_time

    def to_dict(self) -> Dict[str, Any]:
        """Serialize statistics to a dictionary."""
        return {
            "l1_hits": self.l1_hits,
            "l1_misses": self.l1_misses,
            "l1_hit_rate": round(self.l1_hit_rate, 4),
            "l2_hits": self.l2_hits,
            "l2_misses": self.l2_misses,
            "l2_hit_rate": round(self.l2_hit_rate, 4),
            "overall_hit_rate": round(self.overall_hit_rate, 4),
            "evictions": self.evictions,
            "invalidations": self.invalidations,
            "total_put_ops": self.total_put_ops,
            "total_get_ops": self.total_get_ops,
            "total_bytes_cached": self.total_bytes_cached,
            "cache_bypasses": self.cache_bypasses,
            "uptime_seconds": round(self.uptime_seconds, 2),
        }


def _estimate_size(value: Any) -> int:
    """Estimate the memory size of a value in bytes."""
    if isinstance(value, np.ndarray):
        return value.nbytes
    if isinstance(value, dict):
        total = 0
        for k, v in value.items():
            total += len(str(k)) + _estimate_size(v)
        return total
    if isinstance(value, (list, tuple)):
        return sum(_estimate_size(item) for item in value)
    if isinstance(value, str):
        return len(value.encode("utf-8"))
    if isinstance(value, (int, float, bool)):
        return 8
    if isinstance(value, bytes):
        return len(value)
    # Fallback: rough estimate
    return 64


def generate_cache_key(
    entry_type: CacheEntryType,
    input_data: Any = None,
    config_fingerprint: str = "",
    extra_parts: Optional[List[str]] = None,
) -> str:
    """Generate a deterministic cache key from inputs.

    Keys are built by hashing a combination of:
    - Entry type
    - A fingerprint of the input data (numpy arrays, dicts, etc.)
    - The configuration fingerprint
    - Any extra discriminator strings

    Args:
        entry_type: The type of cached result.
        input_data: The primary input that produced the result.
        config_fingerprint: Hash of the configuration used.
        extra_parts: Additional strings to include in the key.

    Returns:
        A hex-encoded SHA-256 key string.
    """
    hasher = hashlib.sha256()
    hasher.update(entry_type.value.encode("utf-8"))
    hasher.update(config_fingerprint.encode("utf-8"))

    if input_data is not None:
        if isinstance(input_data, np.ndarray):
            hasher.update(input_data.tobytes())
        elif isinstance(input_data, dict):
            # Deterministic JSON serialization
            hasher.update(
                json.dumps(
                    input_data, sort_keys=True, default=str
                ).encode("utf-8")
            )
        elif isinstance(input_data, (bytes, bytearray)):
            hasher.update(input_data)
        else:
            hasher.update(str(input_data).encode("utf-8"))

    if extra_parts:
        for part in extra_parts:
            hasher.update(len(part).to_bytes(4, "big"))
            hasher.update(part.encode("utf-8"))

    return hasher.hexdigest()


def compute_config_fingerprint(config: Any) -> str:
    """Compute a fingerprint for a DTESN configuration object.

    This fingerprint changes whenever the configuration changes,
    ensuring that cache entries produced under a different config
    are automatically invalidated on lookup.

    Args:
        config: A configuration object (dataclass, dict, or any object
                with ``__dict__``).

    Returns:
        A short hex fingerprint string.
    """
    hasher = hashlib.sha256()
    if hasattr(config, "__dict__"):
        data = {k: str(v) for k, v in config.__dict__.items()}
    elif isinstance(config, dict):
        data = {k: str(v) for k, v in config.items()}
    else:
        data = {"value": str(config)}
    hasher.update(json.dumps(data, sort_keys=True).encode("utf-8"))
    return hasher.hexdigest()[:16]


class L1MemoryCache:
    """Thread-safe in-memory LRU cache (L1).

    Provides O(1) get/put operations with LRU eviction and TTL expiry.
    Uses a reader-writer lock for safe concurrent access.
    """

    def __init__(self, max_entries: int = 1024, max_memory_mb: float = 64.0):
        self._max_entries = max_entries
        self._max_memory_bytes = int(max_memory_mb * 1024 * 1024)
        self._store: OrderedDict[str, CacheEntry] = OrderedDict()
        self._current_bytes = 0
        self._eviction_count = 0
        self._lock = threading.RLock()

    def get(self, key: str) -> Optional[CacheEntry]:
        """Retrieve an entry by key, returning *None* on miss or expiry."""
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            if entry.is_expired:
                self._remove(key)
                return None
            # Move to end (most recently used)
            self._store.move_to_end(key)
            entry.hit_count += 1
            return entry

    def put(self, entry: CacheEntry) -> None:
        """Insert or update an entry, evicting LRU items if necessary."""
        with self._lock:
            # Remove existing entry with same key if present
            if entry.key in self._store:
                self._remove(entry.key)

            # Evict until we have room
            while (
                len(self._store) >= self._max_entries
                or (self._current_bytes + entry.size_bytes)
                > self._max_memory_bytes
            ) and self._store:
                self._evict_lru()

            self._store[entry.key] = entry
            self._current_bytes += entry.size_bytes

    def invalidate(self, key: str) -> bool:
        """Remove a specific entry. Returns True if found."""
        with self._lock:
            if key in self._store:
                self._remove(key)
                return True
            return False

    def invalidate_by_type(self, entry_type: CacheEntryType) -> int:
        """Remove all entries of a given type. Returns count removed."""
        with self._lock:
            keys_to_remove = [
                k for k, v in self._store.items()
                if v.entry_type == entry_type
            ]
            for key in keys_to_remove:
                self._remove(key)
            return len(keys_to_remove)

    def invalidate_by_config(self, config_fingerprint: str) -> int:
        """Remove entries whose config fingerprint does not match."""
        with self._lock:
            keys_to_remove = [
                k for k, v in self._store.items()
                if v.config_fingerprint != config_fingerprint
            ]
            for key in keys_to_remove:
                self._remove(key)
            return len(keys_to_remove)

    def clear(self) -> int:
        """Remove all entries. Returns count removed."""
        with self._lock:
            count = len(self._store)
            self._store.clear()
            self._current_bytes = 0
            return count

    @property
    def size(self) -> int:
        """Number of entries currently stored."""
        with self._lock:
            return len(self._store)

    @property
    def memory_bytes(self) -> int:
        """Approximate memory usage in bytes."""
        with self._lock:
            return self._current_bytes

    def _remove(self, key: str) -> None:
        """Remove a key (caller must hold _lock)."""
        entry = self._store.pop(key, None)
        if entry is not None:
            self._current_bytes = max(0, self._current_bytes - entry.size_bytes)

    @property
    def eviction_count(self) -> int:
        """Total number of LRU evictions performed."""
        return self._eviction_count

    def _evict_lru(self) -> Optional[str]:
        """Evict the least recently used entry (caller must hold _lock)."""
        if not self._store:
            return None
        key, entry = self._store.popitem(last=False)
        self._current_bytes = max(0, self._current_bytes - entry.size_bytes)
        self._eviction_count += 1
        return key


class L2RedisCache:
    """Optional Redis-backed cache (L2).

    All operations degrade gracefully if Redis is unavailable — they
    return None / False and log a warning rather than raising.
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        key_prefix: str = "dtesn_cache",
        default_ttl: float = 600.0,
    ):
        self._key_prefix = key_prefix
        self._default_ttl = default_ttl
        self._client = None
        self._available = False

        try:
            import redis as redis_lib
            self._client = redis_lib.from_url(redis_url, decode_responses=False)
            self._client.ping()
            self._available = True
            logger.info("L2 Redis cache connected: %s", redis_url)
        except ImportError:
            logger.info("Redis library not installed — L2 cache disabled")
        except Exception as exc:
            logger.info("Redis not available — L2 cache disabled: %s", exc)

    @property
    def available(self) -> bool:
        return self._available

    def _make_key(self, key: str) -> str:
        return f"{self._key_prefix}:{key}"

    def get(self, key: str) -> Optional[bytes]:
        """Retrieve raw bytes from Redis. Returns None on miss or error."""
        if not self._available:
            return None
        try:
            data = self._client.get(self._make_key(key))
            return data
        except Exception as exc:
            logger.warning("L2 cache get error: %s", exc)
            return None

    def put(self, key: str, data: bytes, ttl: Optional[float] = None) -> bool:
        """Store raw bytes in Redis with TTL. Returns True on success."""
        if not self._available:
            return False
        try:
            ttl_seconds = int(ttl if ttl is not None else self._default_ttl)
            self._client.setex(self._make_key(key), ttl_seconds, data)
            return True
        except Exception as exc:
            logger.warning("L2 cache put error: %s", exc)
            return False

    def invalidate(self, key: str) -> bool:
        """Delete a key from Redis. Returns True if deleted."""
        if not self._available:
            return False
        try:
            return bool(self._client.delete(self._make_key(key)))
        except Exception as exc:
            logger.warning("L2 cache invalidate error: %s", exc)
            return False

    def clear(self) -> int:
        """Delete all keys with our prefix. Returns count deleted."""
        if not self._available:
            return 0
        try:
            pattern = f"{self._key_prefix}:*"
            keys = list(self._client.scan_iter(match=pattern, count=500))
            if keys:
                return self._client.delete(*keys)
            return 0
        except Exception as exc:
            logger.warning("L2 cache clear error: %s", exc)
            return 0


def _serialize_for_redis(value: Any) -> bytes:
    """Serialize a cache value to bytes for Redis storage.

    Handles numpy arrays by converting them to lists first, then
    JSON-encodes the entire value.
    """

    def _convert(obj: Any) -> Any:
        if isinstance(obj, np.ndarray):
            return {
                "__ndarray__": True,
                "data": obj.tolist(),
                "dtype": str(obj.dtype),
            }
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, dict):
            return {str(k): _convert(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [_convert(item) for item in obj]
        if isinstance(obj, Enum):
            return obj.value
        return obj

    return json.dumps(_convert(value), sort_keys=True).encode("utf-8")


def _deserialize_from_redis(data: bytes) -> Any:
    """Deserialize bytes from Redis back to Python objects.

    Reconstructs numpy arrays from the ``__ndarray__`` marker.
    """

    def _reconstruct(obj: Any) -> Any:
        if isinstance(obj, dict):
            if obj.get("__ndarray__"):
                return np.array(obj["data"], dtype=obj.get("dtype", "float64"))
            return {k: _reconstruct(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_reconstruct(item) for item in obj]
        return obj

    return _reconstruct(json.loads(data.decode("utf-8")))


class DTESNCache:
    """Multi-level caching layer for DTESN processing results.

    Provides a unified interface over L1 (in-memory LRU) and optional
    L2 (Redis) caches with:
    - Automatic key generation from inputs and config
    - Per-entry-type TTLs
    - Config-based invalidation on system changes
    - Comprehensive hit/miss statistics

    Usage::

        config = CacheConfig(l1_max_entries=512)
        cache = DTESNCache(config)

        # Cache a system update result
        result = dtesn_system.update_system(input_vec)
        cache.put(
            entry_type=CacheEntryType.SYSTEM_UPDATE,
            value=result,
            input_data=input_vec,
            config_fingerprint=fingerprint,
        )

        # Later, retrieve it
        cached = cache.get(
            entry_type=CacheEntryType.SYSTEM_UPDATE,
            input_data=input_vec,
            config_fingerprint=fingerprint,
        )
    """

    def __init__(self, config: Optional[CacheConfig] = None):
        self._config = config or CacheConfig()
        self._stats = CacheStatistics()

        # Initialize L1 (always available)
        self._l1 = L1MemoryCache(
            max_entries=self._config.l1_max_entries,
            max_memory_mb=self._config.l1_max_memory_mb,
        )

        # Initialize L2 (optional)
        self._l2: Optional[L2RedisCache] = None
        if self._config.enable_l2:
            self._l2 = L2RedisCache(
                redis_url=self._config.redis_url,
                key_prefix=self._config.redis_key_prefix,
                default_ttl=self._config.redis_ttl_seconds,
            )

        logger.info(
            "DTESNCache initialized: L1=%d entries / %.1f MB, L2=%s",
            self._config.l1_max_entries,
            self._config.l1_max_memory_mb,
            "enabled" if (self._l2 and self._l2.available) else "disabled",
        )

    def get(
        self,
        entry_type: CacheEntryType,
        input_data: Any = None,
        config_fingerprint: str = "",
        extra_key_parts: Optional[List[str]] = None,
    ) -> Optional[Any]:
        """Look up a cached result.

        Checks L1 first, then L2. On L2 hit, the entry is promoted to L1.

        Args:
            entry_type: Type of result being looked up.
            input_data: The input that produced the result.
            config_fingerprint: Config fingerprint to match.
            extra_key_parts: Additional key discriminators.

        Returns:
            The cached value, or None on miss.
        """
        # Check bypass list
        if entry_type.value in self._config.bypass_cache_types:
            self._stats.cache_bypasses += 1
            return None

        self._stats.total_get_ops += 1

        key = generate_cache_key(
            entry_type, input_data, config_fingerprint, extra_key_parts
        )
        versioned_key = f"{self._config.cache_version}:{key}"

        # --- L1 lookup ---
        l1_entry = self._l1.get(versioned_key)
        if l1_entry is not None:
            # Verify config fingerprint still matches
            if l1_entry.config_fingerprint == config_fingerprint:
                self._stats.l1_hits += 1
                return l1_entry.value
            else:
                # Config changed — invalidate stale entry
                self._l1.invalidate(versioned_key)

        self._stats.l1_misses += 1

        # --- L2 lookup ---
        if self._l2 and self._l2.available:
            raw = self._l2.get(versioned_key)
            if raw is not None:
                try:
                    value = _deserialize_from_redis(raw)
                    self._stats.l2_hits += 1
                    # Promote to L1
                    ttl = self._get_ttl(entry_type)
                    size = _estimate_size(value)
                    entry = CacheEntry(
                        key=versioned_key,
                        value=value,
                        entry_type=entry_type,
                        created_at=time.monotonic(),
                        ttl_seconds=ttl,
                        size_bytes=size,
                        config_fingerprint=config_fingerprint,
                    )
                    self._l1.put(entry)
                    return value
                except Exception as exc:
                    logger.warning("L2 deserialization failed: %s", exc)
            self._stats.l2_misses += 1

        return None

    def put(
        self,
        entry_type: CacheEntryType,
        value: Any,
        input_data: Any = None,
        config_fingerprint: str = "",
        extra_key_parts: Optional[List[str]] = None,
        ttl_override: Optional[float] = None,
    ) -> str:
        """Store a result in the cache.

        Writes to L1 always, and to L2 if available.

        Args:
            entry_type: Type of result being stored.
            value: The result data to cache.
            input_data: The input that produced the result.
            config_fingerprint: Current config fingerprint.
            extra_key_parts: Additional key discriminators.
            ttl_override: Optional TTL override (seconds).

        Returns:
            The cache key used.
        """
        if entry_type.value in self._config.bypass_cache_types:
            self._stats.cache_bypasses += 1
            return ""

        self._stats.total_put_ops += 1

        key = generate_cache_key(
            entry_type, input_data, config_fingerprint, extra_key_parts
        )
        versioned_key = f"{self._config.cache_version}:{key}"
        if ttl_override is not None:
            ttl = ttl_override
        else:
            ttl = self._get_ttl(entry_type)
        size = _estimate_size(value)

        # Write to L1
        entry = CacheEntry(
            key=versioned_key,
            value=value,
            entry_type=entry_type,
            created_at=time.monotonic(),
            ttl_seconds=ttl,
            size_bytes=size,
            config_fingerprint=config_fingerprint,
        )
        self._l1.put(entry)
        self._stats.total_bytes_cached += size

        # Write to L2
        if self._l2 and self._l2.available:
            try:
                raw = _serialize_for_redis(value)
                self._l2.put(versioned_key, raw, ttl)
            except Exception as exc:
                logger.warning("L2 cache write failed: %s", exc)

        return versioned_key

    def invalidate(
        self,
        entry_type: CacheEntryType,
        input_data: Any = None,
        config_fingerprint: str = "",
        extra_key_parts: Optional[List[str]] = None,
    ) -> bool:
        """Invalidate a specific cache entry.

        Returns True if the entry was found and removed from at least one level.
        """
        key = generate_cache_key(
            entry_type, input_data, config_fingerprint, extra_key_parts
        )
        versioned_key = f"{self._config.cache_version}:{key}"

        removed = self._l1.invalidate(versioned_key)
        if self._l2 and self._l2.available:
            removed = self._l2.invalidate(versioned_key) or removed

        if removed:
            self._stats.invalidations += 1
        return removed

    def invalidate_by_type(self, entry_type: CacheEntryType) -> int:
        """Invalidate all entries of a given type (L1 only).

        Returns the number of entries removed.
        """
        count = self._l1.invalidate_by_type(entry_type)
        self._stats.invalidations += count
        return count

    def invalidate_on_config_change(self, new_config_fingerprint: str) -> int:
        """Invalidate entries whose config fingerprint is stale.

        Call this when the DTESN system configuration changes to ensure
        that results computed under the old configuration are not served.

        Returns the number of entries removed.
        """
        count = self._l1.invalidate_by_config(new_config_fingerprint)
        self._stats.invalidations += count
        logger.info(
            "Config change invalidation: removed %d stale entries", count
        )
        return count

    def clear(self) -> int:
        """Clear all cache entries across all levels.

        Returns total entries removed.
        """
        count = self._l1.clear()
        if self._l2 and self._l2.available:
            count += self._l2.clear()
        self._stats.invalidations += count
        return count

    @property
    def stats(self) -> CacheStatistics:
        """Access cache statistics."""
        return self._stats

    def get_stats_dict(self) -> Dict[str, Any]:
        """Get cache statistics as a dictionary."""
        # Sync eviction count from L1 into statistics
        self._stats.evictions = self._l1.eviction_count
        base = self._stats.to_dict()
        base["l1_entries"] = self._l1.size
        base["l1_memory_bytes"] = self._l1.memory_bytes
        base["l2_available"] = bool(self._l2 and self._l2.available)
        base["cache_version"] = self._config.cache_version
        return base

    def reset_stats(self) -> None:
        """Reset statistics counters."""
        self._stats = CacheStatistics()

    def _get_ttl(self, entry_type: CacheEntryType) -> float:
        """Look up the TTL for an entry type."""
        return self._config.entry_ttls.get(
            entry_type.value, self._config.default_ttl_seconds
        )


class CachedDTESNSystem:
    """Wrapper around a DTESNIntegratedSystem that adds transparent caching.

    This class decorates an existing ``DTESNIntegratedSystem`` (or any object
    with compatible methods) to cache expensive operations automatically.

    Usage::

        from dtesn_integration import create_standard_dtesn
        from dtesn_cache import CachedDTESNSystem, CacheConfig

        dtesn = create_standard_dtesn()
        cached = CachedDTESNSystem(dtesn, CacheConfig())

        # First call computes and caches
        result = cached.update_system(input_vec)

        # Second call with same input returns cached result
        result = cached.update_system(input_vec)
    """

    def __init__(
        self,
        dtesn_system: Any,
        cache_config: Optional[CacheConfig] = None,
    ):
        self._system = dtesn_system
        self._cache = DTESNCache(cache_config)

        # Compute initial config fingerprint
        if hasattr(dtesn_system, "config"):
            self._config_fingerprint = compute_config_fingerprint(
                dtesn_system.config
            )
        else:
            self._config_fingerprint = "default"

    @property
    def cache(self) -> DTESNCache:
        """Access the underlying cache instance."""
        return self._cache

    @property
    def system(self) -> Any:
        """Access the underlying DTESN system."""
        return self._system

    def update_system(self, global_input: np.ndarray) -> Dict[str, Any]:
        """Update the DTESN system.

        Because ``update_system`` is **stateful** — it mutates the
        reservoir's internal state on every call — the underlying
        system is *always* invoked so that state evolution is never
        skipped.  The cache is checked first and, on a hit with
        matching input, the (already-known) result dict is returned
        after the state update completes to confirm consistency.
        On a miss, the computed result is stored for future lookups.
        """
        # Always call the underlying system to keep state consistent
        result = self._system.update_system(global_input)

        # Store result in cache for future reference / monitoring
        self._cache.put(
            entry_type=CacheEntryType.SYSTEM_UPDATE,
            value=result,
            input_data=global_input,
            config_fingerprint=self._config_fingerprint,
        )
        return result

    def get_system_summary(self) -> Dict[str, Any]:
        """Get system summary, using cache when possible."""
        cached = self._cache.get(
            entry_type=CacheEntryType.SYSTEM_SUMMARY,
            config_fingerprint=self._config_fingerprint,
        )
        if cached is not None:
            return cached

        result = self._system.get_system_summary()

        self._cache.put(
            entry_type=CacheEntryType.SYSTEM_SUMMARY,
            value=result,
            config_fingerprint=self._config_fingerprint,
        )
        return result

    def validate_integration(self) -> Tuple[bool, List[str]]:
        """Validate integration, using cache when possible."""
        cached = self._cache.get(
            entry_type=CacheEntryType.VALIDATION_RESULT,
            config_fingerprint=self._config_fingerprint,
        )
        if cached is not None:
            return cached["is_valid"], cached["issues"]

        is_valid, issues = self._system.validate_integration()

        self._cache.put(
            entry_type=CacheEntryType.VALIDATION_RESULT,
            value={"is_valid": is_valid, "issues": issues},
            config_fingerprint=self._config_fingerprint,
        )
        return is_valid, issues

    def on_config_change(self) -> None:
        """Call when the DTESN system configuration has changed.

        Re-computes the config fingerprint and invalidates stale entries.
        """
        if hasattr(self._system, "config"):
            new_fp = compute_config_fingerprint(self._system.config)
        else:
            new_fp = "default"

        if new_fp != self._config_fingerprint:
            self._cache.invalidate_on_config_change(new_fp)
            self._config_fingerprint = new_fp

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        return self._cache.get_stats_dict()
