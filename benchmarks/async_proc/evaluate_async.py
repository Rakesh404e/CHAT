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
from models.factory import ModelFactory
from memory.extractor import MemoryExtractor
from memory.short_term import ShortTermMemory
from chatbot.agent import ChatAgent
from tasks.manager import AsyncTaskManager
from config import Config
from benchmarks.common.benchmark_runner import calculate_quantiles, BenchmarkResultCollector
from benchmarks.memory.evaluate_memory_extraction import ResilientBenchmarkModel


def run_async_processing_benchmark(num_runs: int = 10):
    print("=" * 70)
    print(f"RUNNING PHASE 9 — ASYNC / BACKGROUND PROCESSING BENCHMARK ({num_runs} RUNS)")
    print("=" * 70)

    temp_dir = tempfile.mkdtemp(prefix="benchmark_async_")
    db_path = os.path.join(temp_dir, "test_async.db")
    chroma_path = os.path.join(temp_dir, "test_chroma")

    try:
        config = Config()
        config.database_path = db_path
        config.chroma_path = chroma_path

        db = Database(db_path=db_path)
        db.initialize()
        chat_store = ChatStore(db)

        vector_store = ChromaVectorStore(path=chroma_path, collection_name="test_async")
        embedding_model = EmbeddingFactory.create(config)
        raw_model = ModelFactory.create(config)
        model = ResilientBenchmarkModel(raw_model)
        extractor = MemoryExtractor(model=model)

        user_id = chat_store.create_user()
        conv_id = chat_store.create_conversation(user_id, "Async Test Session")

        ltm = LongTermMemory(
            chat_store=chat_store,
            user_id=user_id,
            vector_store=vector_store,
            embedding_model=embedding_model
        )

        task_mgr = AsyncTaskManager(max_workers=4)

        sync_latencies_ms = []
        async_latencies_ms = []
        background_job_latencies_ms = []
        async_failures = 0

        message = "I prefer Python and plan to build a microservice with FastAPI and Docker."

        for run in range(1, num_runs + 1):
            agent_sync = ChatAgent(
                model=model,
                memory=ShortTermMemory(),
                chat_store=chat_store,
                conversation_id=conv_id,
                long_term_memory=ltm,
                extractor=extractor,
                async_processing=False
            )
            agent_sync.load_context()

            t0 = time.time()
            agent_sync.chat(message, async_processing=False)
            t1 = time.time()
            sync_latencies_ms.append((t1 - t0) * 1000)

            agent_async = ChatAgent(
                model=model,
                memory=ShortTermMemory(),
                chat_store=chat_store,
                conversation_id=conv_id,
                long_term_memory=ltm,
                extractor=extractor,
                task_manager=task_mgr,
                async_processing=True
            )
            agent_async.load_context()

            t0 = time.time()
            response = agent_async.chat(message, async_processing=True)
            t1 = time.time()
            async_user_perceived = (t1 - t0) * 1000
            async_latencies_ms.append(async_user_perceived)

            t_bg_start = time.time()
            success = agent_async.wait_for_background_tasks(timeout=10.0)
            t_bg_end = time.time()

            if not success:
                async_failures += 1

            task_id = agent_async.get_last_task_id()
            if task_id:
                rec = task_mgr.get_task(task_id)
                if rec and rec.duration_ms is not None:
                    background_job_latencies_ms.append(rec.duration_ms)
                else:
                    background_job_latencies_ms.append((t_bg_end - t_bg_start) * 1000)

        sync_q = calculate_quantiles(sync_latencies_ms)
        async_q = calculate_quantiles(async_latencies_ms)
        bg_q = calculate_quantiles(background_job_latencies_ms)

        latency_reduction_percent = round(100.0 * (sync_q["p50"] - async_q["p50"]) / sync_q["p50"], 2) if sync_q["p50"] > 0 else 0.0

        collector = BenchmarkResultCollector()
        collector.add_result("sync_user_latency_p50", sync_q["p50"], "ms", "async_processing", num_runs)
        collector.add_result("async_user_latency_p50", async_q["p50"], "ms", "async_processing", num_runs)
        collector.add_result("sync_user_latency_p95", sync_q["p95"], "ms", "async_processing", num_runs)
        collector.add_result("async_user_latency_p95", async_q["p95"], "ms", "async_processing", num_runs)
        collector.add_result("async_latency_reduction_pct", latency_reduction_percent, "percent", "async_processing", num_runs)
        collector.add_result("background_job_duration_p50", bg_q["p50"], "ms", "async_processing", num_runs)
        collector.add_result("background_job_duration_p95", bg_q["p95"], "ms", "async_processing", num_runs)
        collector.add_result("background_task_failures", async_failures, "count", "async_processing", num_runs)

        print("\n--- ASYNC vs SYNC PROCESSING COMPARISON ---")
        print(f"Sync User-Perceived Latency  -> P50: {sync_q['p50']} ms | P95: {sync_q['p95']} ms | Mean: {sync_q['mean']} ms")
        print(f"Async User-Perceived Latency -> P50: {async_q['p50']} ms | P95: {async_q['p95']} ms | Mean: {async_q['mean']} ms")
        print(f"Background Job Processing    -> P50: {bg_q['p50']} ms | P95: {bg_q['p95']} ms")
        print(f"Latency Reduction Percentage : {latency_reduction_percent}%")
        print(f"Background Task Failures     : {async_failures}")

        task_mgr.shutdown(wait=True)
        return collector.get_results()

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    run_async_processing_benchmark()
