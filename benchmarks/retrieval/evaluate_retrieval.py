import os
import sys
import json
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
from config import Config
from benchmarks.common.benchmark_runner import calculate_quantiles, BenchmarkResultCollector


def run_retrieval_benchmark():
    print("=" * 70)
    print("RUNNING PHASE 3 — RETRIEVAL EVALUATION BENCHMARK")
    print("=" * 70)

    temp_dir = tempfile.mkdtemp(prefix="benchmark_retrieval_")
    db_path = os.path.join(temp_dir, "test_retrieval.db")
    chroma_path = os.path.join(temp_dir, "test_chroma")

    try:
        config = Config()
        config.database_path = db_path
        config.chroma_path = chroma_path

        db = Database(db_path=db_path)
        db.initialize()
        chat_store = ChatStore(db)

        # Create explicit users in SQLite database to satisfy foreign keys
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO users (id) VALUES (101)")
        cursor.execute("INSERT OR IGNORE INTO users (id) VALUES (102)")
        conn.commit()
        conn.close()

        vector_store = ChromaVectorStore(path=chroma_path, collection_name="test_retrieval")
        embedding_model = EmbeddingFactory.create(config)

        dataset_path = workspace_dir / "benchmarks" / "datasets" / "golden_retrieval_dataset.json"
        with open(dataset_path, "r", encoding="utf-8") as f:
            dataset = json.load(f)

        ltm_user_a = LongTermMemory(
            chat_store=chat_store,
            user_id=101,
            vector_store=vector_store,
            embedding_model=embedding_model
        )

        ltm_user_b = LongTermMemory(
            chat_store=chat_store,
            user_id=102,
            vector_store=vector_store,
            embedding_model=embedding_model
        )

        print("Populating 40 User A memories and 20 User B memories...")
        user_a_mem_ids = {}
        for mem in dataset["user_a_memories"]:
            m_id = ltm_user_a.add_or_update_memory(
                memory_type=mem["type"],
                key=mem["key"],
                value=mem["value"],
                scope=mem["scope"]
            )
            user_a_mem_ids[mem["key"]] = m_id

        user_b_mem_ids = {}
        for mem in dataset["user_b_memories"]:
            m_id = ltm_user_b.add_or_update_memory(
                memory_type=mem["type"],
                key=mem["key"],
                value=mem["value"],
                scope=mem["scope"]
            )
            user_b_mem_ids[mem["key"]] = m_id

        print("Populated memory stores cleanly.")

        queries = dataset["test_queries"]
        total_queries = len(queries)

        r1_hits = 0
        r3_hits = 0
        r5_hits = 0
        reciprocal_ranks = []
        zero_retrievals = 0
        total_retrieved_counts = []
        latencies_ms = []
        isolation_failures = 0

        # Perform 5 warmup queries first to stabilize search
        for q in queries[:5]:
            ltm_user_a.search_memories(q["query"], top_k=5)

        for i, q_item in enumerate(queries, start=1):
            query = q_item["query"]
            user_id = q_item["expected_user_id"]
            expected_key = q_item["expected_key"]
            expected_str = q_item["expected_contains"].lower()

            ltm = ltm_user_a if user_id == 101 else ltm_user_b

            if hasattr(ltm, "query_cache") and ltm.query_cache:
                ltm.query_cache.clear()

            t0 = time.time()
            results = ltm.search_memories(query, top_k=5)
            t1 = time.time()

            latency_ms = (t1 - t0) * 1000
            latencies_ms.append(latency_ms)
            total_retrieved_counts.append(len(results))

            if not results:
                zero_retrievals += 1

            for res in results:
                res_user = res.get("metadata", {}).get("user_id")
                if res_user is not None and int(res_user) != user_id:
                    isolation_failures += 1

            found_rank = 0
            for rank, item in enumerate(results, start=1):
                doc_text = item.get("content", "").lower()
                meta_key = item.get("metadata", {}).get("key", "").lower()

                if meta_key == expected_key.lower() or expected_str in doc_text:
                    found_rank = rank
                    break

            if found_rank == 1:
                r1_hits += 1
                r3_hits += 1
                r5_hits += 1
                reciprocal_ranks.append(1.0)
            elif found_rank in (2, 3):
                r3_hits += 1
                r5_hits += 1
                reciprocal_ranks.append(1.0 / found_rank)
            elif found_rank in (4, 5):
                r5_hits += 1
                reciprocal_ranks.append(1.0 / found_rank)
            else:
                reciprocal_ranks.append(0.0)

        recall_1 = round((r1_hits / total_queries) * 100, 2)
        recall_3 = round((r3_hits / total_queries) * 100, 2)
        recall_5 = round((r5_hits / total_queries) * 100, 2)
        mrr = round(sum(reciprocal_ranks) / total_queries, 4)
        avg_retrieved = round(sum(total_retrieved_counts) / total_queries, 2)
        latency_stats = calculate_quantiles(latencies_ms)

        collector = BenchmarkResultCollector()
        collector.add_result("total_queries", total_queries, "count", "retrieval", total_queries, notes="Synthetic evaluation dataset")
        collector.add_result("recall_at_1", recall_1, "percent", "retrieval", total_queries)
        collector.add_result("recall_at_3", recall_3, "percent", "retrieval", total_queries)
        collector.add_result("recall_at_5", recall_5, "percent", "retrieval", total_queries)
        collector.add_result("mrr", mrr, "score", "retrieval", total_queries)
        collector.add_result("zero_retrieval_queries", zero_retrievals, "count", "retrieval", total_queries)
        collector.add_result("user_isolation_failures", isolation_failures, "count", "retrieval", total_queries)
        collector.add_result("avg_retrieved_memories", avg_retrieved, "count", "retrieval", total_queries)
        collector.add_result("retrieval_latency_p50", latency_stats["p50"], "ms", "retrieval", total_queries)
        collector.add_result("retrieval_latency_p95", latency_stats["p95"], "ms", "retrieval", total_queries)
        collector.add_result("retrieval_latency_p99", latency_stats["p99"], "ms", "retrieval", total_queries)
        collector.add_result("retrieval_latency_mean", latency_stats["mean"], "ms", "retrieval", total_queries)

        print("\n--- RETRIEVAL EVALUATION RESULTS ---")
        print(f"Total Queries: {total_queries}")
        print(f"Recall@1: {recall_1}%")
        print(f"Recall@3: {recall_3}%")
        print(f"Recall@5: {recall_5}%")
        print(f"MRR: {mrr}")
        print(f"Zero Retrievals: {zero_retrievals}")
        print(f"User Isolation Failures: {isolation_failures}")
        print(f"Avg Retrieved Items: {avg_retrieved}")
        print(f"Latency P50: {latency_stats['p50']} ms | P95: {latency_stats['p95']} ms | P99: {latency_stats['p99']} ms | Mean: {latency_stats['mean']} ms")

        return collector.get_results()

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    run_retrieval_benchmark()
