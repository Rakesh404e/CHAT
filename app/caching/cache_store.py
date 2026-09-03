import time
import threading
from typing import Any, Dict, Optional, Tuple


class TTLCache:
    """
    Thread-safe In-Memory Cache with Time-To-Live (TTL) expiration,
    maximum capacity eviction, and pattern/user invalidation.
    """

    def __init__(self, maxsize: int = 1000, ttl_seconds: float = 300.0):
        self.maxsize = maxsize
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Tuple[Any, float]] = {}  # key -> (value, expiry_timestamp)
        self._lock = threading.RLock()
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key not in self._cache:
                self.misses += 1
                return None

            value, expiry = self._cache[key]
            if time.time() > expiry:
                del self._cache[key]
                self.misses += 1
                return None

            self.hits += 1
            return value

    def set(self, key: str, value: Any, ttl: Optional[float] = None):
        with self._lock:
            ttl_val = ttl if ttl is not None else self.ttl_seconds
            expiry = time.time() + ttl_val

            # Evict oldest item if capacity is reached
            if len(self._cache) >= self.maxsize and key not in self._cache:
                # Remove first inserted item (FIFO eviction fallback)
                first_key = next(iter(self._cache))
                del self._cache[first_key]

            self._cache[key] = (value, expiry)

    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def invalidate_prefix(self, prefix: str) -> int:
        """
        Invalidates all cache entries starting with the given prefix.
        """
        with self._lock:
            keys_to_delete = [k for k in self._cache.keys() if k.startswith(prefix)]
            for k in keys_to_delete:
                del self._cache[k]
            return len(keys_to_delete)

    def clear(self):
        with self._lock:
            self._cache.clear()
            self.hits = 0
            self.misses = 0

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            total_requests = self.hits + self.misses
            hit_rate = round((self.hits / total_requests) * 100, 2) if total_requests > 0 else 0.0
            return {
                "active_items": len(self._cache),
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate_pct": hit_rate
            }
