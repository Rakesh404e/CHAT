from typing import List, Dict, Any, Optional
from caching.cache_store import TTLCache
from observability.metrics import metrics_collector
from observability.logger import logger


class MemoryQueryCache:
    """
    Query cache manager for Long-Term Memory search results.
    Caches hybrid retrieval results per user and handles automated invalidation on memory mutations.
    """

    def __init__(self, maxsize: int = 2000, ttl_seconds: float = 600.0):
        self.cache = TTLCache(maxsize=maxsize, ttl_seconds=ttl_seconds)

    def _build_key(self, user_id: int, query: str, top_k: int, min_score: float) -> str:
        clean_query = query.strip().lower()
        return f"mem_search:{user_id}:{clean_query}:{top_k}:{min_score}"

    def get(self, user_id: int, query: str, top_k: int = 5, min_score: float = 0.0) -> Optional[List[Dict[str, Any]]]:
        key = self._build_key(user_id, query, top_k, min_score)
        results = self.cache.get(key)
        if results is not None:
            metrics_collector.record_cache_hit("memory_search")
            logger.debug(f"Memory search cache HIT for user {user_id}", user_id=user_id, query=query)
            return results
        metrics_collector.record_cache_miss("memory_search")
        return None

    def set(self, user_id: int, query: str, top_k: int, min_score: float, results: List[Dict[str, Any]]):
        key = self._build_key(user_id, query, top_k, min_score)
        self.cache.set(key, results)

    def invalidate_user(self, user_id: int) -> int:
        prefix = f"mem_search:{user_id}:"
        count = self.cache.invalidate_prefix(prefix)
        logger.info(f"Invalidated {count} cached memory queries for user {user_id}", user_id=user_id)
        return count

    def clear(self):
        self.cache.clear()

    def get_stats(self) -> dict:
        return self.cache.get_stats()
