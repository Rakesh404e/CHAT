from typing import Dict, Any, List


class MetricsCollector:
    """
    In-Memory Metrics Collector for recording latencies, call counts, errors,
    and memory operations across the AI Agent lifecycle.
    """

    def __init__(self):
        self.reset()

    def reset(self):
        self.llm_calls_total = 0
        self.llm_errors_total = 0
        self.llm_latencies_ms: List[float] = []

        self.embedding_calls_total = 0
        self.embedding_errors_total = 0
        self.embedding_latencies_ms: List[float] = []

        self.memory_searches_total = 0
        self.memory_hits_total = 0
        self.memory_deletions_total = 0

        self.retries_total = 0

        self.cache_hits_total = 0
        self.cache_misses_total = 0
        self.cache_hits_by_type: Dict[str, int] = {}

    def record_llm_call(self, duration_ms: float, success: bool = True):
        self.llm_calls_total += 1
        if success:
            self.llm_latencies_ms.append(duration_ms)
        else:
            self.llm_errors_total += 1

    def record_embedding_call(self, duration_ms: float, success: bool = True):
        self.embedding_calls_total += 1
        if success:
            self.embedding_latencies_ms.append(duration_ms)
        else:
            self.embedding_errors_total += 1

    def record_memory_search(self, hit_count: int):
        self.memory_searches_total += 1
        if hit_count > 0:
            self.memory_hits_total += 1

    def record_memory_deletion(self, count: int = 1):
        self.memory_deletions_total += count

    def record_retry(self):
        self.retries_total += 1

    def record_cache_hit(self, cache_type: str = "general"):
        self.cache_hits_total += 1
        self.cache_hits_by_type[cache_type] = self.cache_hits_by_type.get(cache_type, 0) + 1

    def record_cache_miss(self, cache_type: str = "general"):
        self.cache_misses_total += 1

    def get_metrics_summary(self) -> Dict[str, Any]:
        avg_llm_latency = (
            round(sum(self.llm_latencies_ms) / len(self.llm_latencies_ms), 2)
            if self.llm_latencies_ms else 0.0
        )
        avg_embedding_latency = (
            round(sum(self.embedding_latencies_ms) / len(self.embedding_latencies_ms), 2)
            if self.embedding_latencies_ms else 0.0
        )
        hit_rate = (
            round((self.memory_hits_total / self.memory_searches_total) * 100, 2)
            if self.memory_searches_total > 0 else 0.0
        )
        total_cache_reqs = self.cache_hits_total + self.cache_misses_total
        cache_hit_rate = (
            round((self.cache_hits_total / total_cache_reqs) * 100, 2)
            if total_cache_reqs > 0 else 0.0
        )

        return {
            "llm": {
                "calls_total": self.llm_calls_total,
                "errors_total": self.llm_errors_total,
                "avg_latency_ms": avg_llm_latency
            },
            "embedding": {
                "calls_total": self.embedding_calls_total,
                "errors_total": self.embedding_errors_total,
                "avg_latency_ms": avg_embedding_latency
            },
            "memory": {
                "searches_total": self.memory_searches_total,
                "hits_total": self.memory_hits_total,
                "hit_rate_pct": hit_rate,
                "deletions_total": self.memory_deletions_total
            },
            "cache": {
                "hits_total": self.cache_hits_total,
                "misses_total": self.cache_misses_total,
                "hit_rate_pct": cache_hit_rate,
                "hits_by_type": self.cache_hits_by_type
            },
            "reliability": {
                "retries_total": self.retries_total
            }
        }


# Global metrics collector instance
metrics_collector = MetricsCollector()

