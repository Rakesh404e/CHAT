import hashlib
from typing import List, Optional
from embeddings.base import EmbeddingModel
from caching.cache_store import TTLCache
from observability.metrics import metrics_collector
from observability.logger import logger


class CachedEmbeddingModel(EmbeddingModel):
    """
    Caching decorator wrapper for EmbeddingModel instances.
    Skips redundant API calls for previously embedded texts.
    """

    def __init__(self, embedding_model: EmbeddingModel, maxsize: int = 5000, ttl_seconds: float = 86400.0):
        self.embedding_model = embedding_model
        self.cache = TTLCache(maxsize=maxsize, ttl_seconds=ttl_seconds)

    def _hash_text(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def embed(self, text: str, trace_id: Optional[str] = None) -> List[float]:
        cache_key = self._hash_text(text)
        cached_vector = self.cache.get(cache_key)

        if cached_vector is not None:
            metrics_collector.record_cache_hit("embedding")
            logger.debug("Embedding cache HIT", trace_id=trace_id)
            return cached_vector

        metrics_collector.record_cache_miss("embedding")
        logger.debug("Embedding cache MISS - generating vector", trace_id=trace_id)

        if (
            hasattr(self.embedding_model, "embed")
            and hasattr(self.embedding_model.embed, "__code__")
            and "trace_id" in self.embedding_model.embed.__code__.co_varnames
        ):
            vector = self.embedding_model.embed(text, trace_id=trace_id)
        else:
            vector = self.embedding_model.embed(text)


        self.cache.set(cache_key, vector)
        return vector

    def get_cache_stats(self) -> dict:
        return self.cache.get_stats()
