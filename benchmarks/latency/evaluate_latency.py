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
from memory.sumarizer import Summarizer
from chatbot.agent import ChatAgent
from config import Config
from benchmarks.common.benchmark_runner import calculate_quantiles, BenchmarkResultCollector
from benchmarks.memory.evaluate_memory_extraction import ResilientBenchmarkModel


def run_latency_benchmark(num_runs: int = 15):
    print("=" * 70)
    print(f"RUNNING PHASE 8 — LATENCY BREAKDOWN BENCHMARK ({num_runs} RUNS)")
    print("=" * 70)

    temp_dir = tempfile.mkdtemp(prefix="benchmark_latency_")
    db_path = os.path.join(temp_dir, "test_latency.db")
    chroma_path = os.path.join(temp_dir, "test_chroma")

    try:
        config = Config()
        config.database_path = db_path
        config.chroma_path = chroma_path

        db = Database(db_path=db_path)
        db.initialize()
        chat_store = ChatStore(db)

        vector_store = ChromaVectorStore(path=chroma_path, collection_name="test_latency")
        embedding_model = EmbeddingFactory.create(config)
        raw_model = ModelFactory.create(config)
        model = ResilientBenchmarkModel(raw_model)
        extractor = MemoryExtractor(model=model)
        summarizer = Summarizer(model=model)

        user_id = chat_store.create_user()
        conv_id = chat_store.create_conversation(user_id, "Latency Test Conversation")

        ltm = LongTermMemory(
            chat_store=chat_store,
            user_id=user_id,
            vector_store=vector_store,
            embedding_model=embedding_model
        )

        ltm.add_or_update_memory("preference", "language", "Python")
        ltm.add_or_update_memory("goal", "target_role", "Senior AI Engineer")

        embedding_model.embed("warmup text")
        ltm.search_memories("warmup", top_k=5)

        db_latencies = []
        embed_latencies = []
        vector_latencies = []
        llm_latencies = []
        extraction_latencies = []
        summarization_latencies = []
        e2e_latencies = []

        test_message = "I prefer using FastAPI and Python for building scalable AI agent microservices."

        for run in range(1, num_runs + 1):
            t0 = time.time()
            msg_id = chat_store.save_message(conv_id, "user", f"Test message run {run}")
            recent = chat_store.get_recent_messages(conv_id, limit=5)
            t1 = time.time()
            db_latencies.append((t1 - t0) * 1000)

            t0 = time.time()
            vector = embedding_model.embed(test_message)
            t1 = time.time()
            embed_latencies.append((t1 - t0) * 1000)

            t0 = time.time()
            v_results = vector_store.search(vector=vector, user_id=user_id, top_k=5)
            t1 = time.time()
            vector_latencies.append((t1 - t0) * 1000)

            t0 = time.time()
            llm_res = model.generate([{"role": "user", "content": test_message}])
            t1 = time.time()
            llm_latencies.append((t1 - t0) * 1000)

            t0 = time.time()
            extracted = extractor.extract(test_message)
            t1 = time.time()
            extraction_latencies.append((t1 - t0) * 1000)

            t0 = time.time()
            summary = summarizer.summarize("", recent)
            t1 = time.time()
            summarization_latencies.append((t1 - t0) * 1000)

            agent = ChatAgent(
                model=model,
                memory=chat_store.get_memories(user_id),
                chat_store=chat_store,
                conversation_id=conv_id,
                long_term_memory=ltm,
                extractor=extractor,
                async_processing=False
            )
            from memory.short_term import ShortTermMemory
            agent.memory = ShortTermMemory()
            agent.load_context()

            t0 = time.time()
            agent.chat(test_message, async_processing=False)
            t1 = time.time()
            e2e_latencies.append((t1 - t0) * 1000)

        db_q = calculate_quantiles(db_latencies)
        embed_q = calculate_quantiles(embed_latencies)
        vector_q = calculate_quantiles(vector_latencies)
        llm_q = calculate_quantiles(llm_latencies)
        ext_q = calculate_quantiles(extraction_latencies)
        sum_q = calculate_quantiles(summarization_latencies)
        e2e_q = calculate_quantiles(e2e_latencies)

        collector = BenchmarkResultCollector()
        
        components = [
            ("sqlite_database", db_q),
            ("embedding_model", embed_q),
            ("chroma_vector_store", vector_q),
            ("llm_generation", llm_q),
            ("memory_extraction", ext_q),
            ("summarization", sum_q),
            ("end_to_end_chat_turn_sync", e2e_q)
        ]

        print("\n--- LATENCY BENCHMARK BREAKDOWN (Local Execution, ms) ---")
        print(f"{'Component':<30} | {'P50':<8} | {'P95':<8} | {'P99':<8} | {'Mean':<8}")
        print("-" * 75)

        for comp_name, q in components:
            print(f"{comp_name:<30} | {q['p50']:<8.2f} | {q['p95']:<8.2f} | {q['p99']:<8.2f} | {q['mean']:<8.2f}")
            collector.add_result(f"latency_{comp_name}_p50", q["p50"], "ms", "latency", num_runs)
            collector.add_result(f"latency_{comp_name}_p95", q["p95"], "ms", "latency", num_runs)
            collector.add_result(f"latency_{comp_name}_p99", q["p99"], "ms", "latency", num_runs)
            collector.add_result(f"latency_{comp_name}_mean", q["mean"], "ms", "latency", num_runs)

        return collector.get_results()

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    run_latency_benchmark()
