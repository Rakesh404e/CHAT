import os
import sys
import time
import shutil
import tempfile
from pathlib import Path

workspace_dir = Path(__file__).resolve().parent.parent.parent
app_dir = workspace_dir / "app"
sys.path.insert(0, str(app_dir))
sys.path.insert(0, str(workspace_dir))

from memory.database import Database
from memory.chat_store import ChatStore
from memory.long_term import LongTermMemory
from vector_store.chroma_store import ChromaVectorStore
from embeddings.factory import EmbeddingFactory
from caching.memory_cache import MemoryQueryCache
from caching.embedding_cache import CachedEmbeddingModel
from config import Config
from benchmarks.common.benchmark_runner import calculate_quantiles, BenchmarkResultCollector


def run_caching_benchmark(num_runs: int = 40):
    print("=" * 70)
    print(f"RUNNING PHASE 10 — CACHING EVALUATION BENCHMARK ({num_runs} ITERATIONS)")
    print("=" * 70)

    temp_dir = tempfile.mkdtemp(prefix="benchmark_cache_")
    db_path = os.path.join(temp_dir, "test_cache.db")
    chroma_path = os.path.join(temp_dir, "test_chroma")

    try:
        config = Config()
        db = Database(db_path=db_path)
        db.initialize()
        chat_store = ChatStore(db)

        user_id = 301
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO users (id) VALUES (?)", (user_id,))
        conn.commit()
        conn.close()

        vector_store = ChromaVectorStore(path=chroma_path, collection_name="test_cache")
        raw_embedding_model = EmbeddingFactory.create(config)
        cached_embedder = CachedEmbeddingModel(raw_embedding_model)

        ltm = LongTermMemory(
            chat_store=chat_store,
            user_id=user_id,
            vector_store=vector_store,
            embedding_model=cached_embedder,
            query_cache=MemoryQueryCache()
        )

        ltm.add_or_update_memory("preference", "programming_language", "Python")
        ltm.add_or_update_memory("goal", "target_role", "Senior AI Engineer")
        ltm.add_or_update_memory("fact", "location", "Seattle")

        query = "What programming language and target role do I have?"

        ltm.query_cache.clear()
        uncached_latencies = []
        for _ in range(num_runs):
            ltm.query_cache.clear()
            t0 = time.time()
            res = ltm.search_memories(query, top_k=5)
            t1 = time.time()
            uncached_latencies.append((t1 - t0) * 1000)

        ltm.search_memories(query, top_k=5)
        cached_latencies = []
        for _ in range(num_runs):
            t0 = time.time()
            res = ltm.search_memories(query, top_k=5)
            t1 = time.time()
            cached_latencies.append((t1 - t0) * 1000)

        uncached_q = calculate_quantiles(uncached_latencies)
        cached_q = calculate_quantiles(cached_latencies)

        speedup = round(uncached_q["p50"] / cached_q["p50"], 2) if cached_q["p50"] > 0 else 1.0

        ltm.query_cache.clear()
        for _ in range(10):
            ltm.search_memories("What is my location?", top_k=3)

        cache_stats = ltm.query_cache.get_stats()
        hit_rate_pct = cache_stats.get("hit_rate_pct", 0.0)

        res1 = ltm.search_memories("programming_language", top_k=5)
        ltm.add_or_update_memory("preference", "programming_language", "Go")
        res2 = ltm.search_memories("programming_language", top_k=5)

        invalidation_correct = False
        if res2 and any("Go" in item.get("content", "") for item in res2):
            invalidation_correct = True

        collector = BenchmarkResultCollector()
        collector.add_result("uncached_retrieval_latency_p50", uncached_q["p50"], "ms", "caching", num_runs)
        collector.add_result("cached_retrieval_latency_p50", cached_q["p50"], "ms", "caching", num_runs)
        collector.add_result("caching_speedup_factor", speedup, "x", "caching", num_runs)
        collector.add_result("cache_hit_rate_pct", hit_rate_pct, "percent", "caching", 10)
        collector.add_result("cache_hits_total", cache_stats.get("hits", 0), "count", "caching", 10)
        collector.add_result("cache_misses_total", cache_stats.get("misses", 0), "count", "caching", 10)
        collector.add_result("cache_invalidation_correctness", 1 if invalidation_correct else 0, "boolean", "caching", 1)

        print("\n--- CACHING BENCHMARK RESULTS ---")
        print(f"Uncached Latency P50: {uncached_q['p50']} ms | P95: {uncached_q['p95']} ms")
        print(f"Cached Latency P50  : {cached_q['p50']} ms | P95: {cached_q['p95']} ms")
        print(f"Speedup Factor      : {speedup}x")
        print(f"Observed Hit Rate   : {hit_rate_pct}% ({cache_stats.get('hits')} hits, {cache_stats.get('misses')} misses)")
        print(f"Invalidation Correctness: {'PASSED' if invalidation_correct else 'FAILED'}")

        return collector.get_results()

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    run_caching_benchmark()
