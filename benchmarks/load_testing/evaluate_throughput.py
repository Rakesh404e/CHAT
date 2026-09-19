import os
import sys
import time
import shutil
import tempfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

workspace_dir = Path(__file__).resolve().parent.parent.parent
app_dir = workspace_dir / "app"
sys.path.insert(0, str(app_dir))
sys.path.insert(0, str(workspace_dir))

from memory.database import Database
from memory.chat_store import ChatStore
from memory.long_term import LongTermMemory
from vector_store.chroma_store import ChromaVectorStore
from embeddings.factory import EmbeddingFactory
from models.factory import ModelFactory
from memory.extractor import MemoryExtractor
from memory.short_term import ShortTermMemory
from chatbot.agent import ChatAgent
from tasks.manager import AsyncTaskManager
from config import Config
from benchmarks.common.benchmark_runner import calculate_quantiles, BenchmarkResultCollector
from benchmarks.memory.evaluate_memory_extraction import ResilientBenchmarkModel


def run_throughput_benchmark(concurrency_levels=[1, 3, 5], requests_per_level=5):
    print("=" * 70)
    print("RUNNING PHASE 15 — LOCAL THROUGHPUT & CONCURRENCY BENCHMARK")
    print("=" * 70)

    temp_dir = tempfile.mkdtemp(prefix="benchmark_throughput_")
    db_path = os.path.join(temp_dir, "test_throughput.db")
    chroma_path = os.path.join(temp_dir, "test_chroma")

    try:
        config = Config()
        config.database_path = db_path
        config.chroma_path = chroma_path

        db = Database(db_path=db_path)
        db.initialize()
        chat_store = ChatStore(db)

        vector_store = ChromaVectorStore(path=chroma_path, collection_name="test_throughput")
        embedding_model = EmbeddingFactory.create(config)
        raw_model = ModelFactory.create(config)
        model = ResilientBenchmarkModel(raw_model)
        extractor = MemoryExtractor(model=model)
        task_mgr = AsyncTaskManager(max_workers=8)

        collector = BenchmarkResultCollector()

        for num_threads in concurrency_levels:
            print(f"\nEvaluating Concurrency Level = {num_threads} threads ({requests_per_level} total requests):")
            
            user_id = chat_store.create_user()
            conv_id = chat_store.create_conversation(user_id, f"Concurrency {num_threads}")
            ltm = LongTermMemory(chat_store=chat_store, user_id=user_id, vector_store=vector_store, embedding_model=embedding_model)

            agent = ChatAgent(
                model=model,
                memory=ShortTermMemory(),
                chat_store=chat_store,
                conversation_id=conv_id,
                long_term_memory=ltm,
                extractor=extractor,
                task_manager=task_mgr,
                async_processing=True
            )
            agent.load_context()

            def _send_req(idx: int):
                t0 = time.time()
                try:
                    res = agent.chat(f"Concurrent message {idx} from thread {num_threads}", async_processing=True)
                    t1 = time.time()
                    return (t1 - t0) * 1000, True, None
                except Exception as e:
                    t1 = time.time()
                    return (t1 - t0) * 1000, False, str(e)

            t_start = time.time()
            latencies = []
            successes = 0
            failures = 0

            with ThreadPoolExecutor(max_workers=num_threads) as pool:
                futures = [pool.submit(_send_req, i) for i in range(requests_per_level)]
                for fut in as_completed(futures):
                    dur_ms, ok, err = fut.result()
                    latencies.append(dur_ms)
                    if ok:
                        successes += 1
                    else:
                        failures += 1

            t_end = time.time()
            total_duration_sec = t_end - t_start
            rps = round(requests_per_level / total_duration_sec, 2) if total_duration_sec > 0 else 0.0
            error_rate_pct = round((failures / requests_per_level) * 100, 2)

            q_lat = calculate_quantiles(latencies)

            print(f"  RPS (Requests/Sec)  : {rps}")
            print(f"  P50 Latency        : {q_lat['p50']} ms")
            print(f"  P95 Latency        : {q_lat['p95']} ms")
            print(f"  Error Rate         : {error_rate_pct}% ({failures}/{requests_per_level})")

            collector.add_result(f"throughput_rps_concurrency_{num_threads}", rps, "req/sec", "throughput", requests_per_level)
            collector.add_result(f"latency_p50_concurrency_{num_threads}", q_lat["p50"], "ms", "throughput", requests_per_level)
            collector.add_result(f"latency_p95_concurrency_{num_threads}", q_lat["p95"], "ms", "throughput", requests_per_level)
            collector.add_result(f"error_rate_concurrency_{num_threads}", error_rate_pct, "percent", "throughput", requests_per_level)

        task_mgr.shutdown(wait=True)
        return collector.get_results()

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    run_throughput_benchmark()
