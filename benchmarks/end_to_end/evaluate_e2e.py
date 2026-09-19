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


def run_e2e_benchmark(num_turns: int = 6):
    print("=" * 70)
    print(f"RUNNING PHASE 13 — END-TO-END MULTI-TURN BENCHMARK ({num_turns} TURNS)")
    print("=" * 70)

    temp_dir = tempfile.mkdtemp(prefix="benchmark_e2e_")
    db_path = os.path.join(temp_dir, "test_e2e.db")
    chroma_path = os.path.join(temp_dir, "test_chroma")

    try:
        config = Config()
        config.database_path = db_path
        config.chroma_path = chroma_path

        db = Database(db_path=db_path)
        db.initialize()
        chat_store = ChatStore(db)

        vector_store = ChromaVectorStore(path=chroma_path, collection_name="test_e2e")
        embedding_model = EmbeddingFactory.create(config)
        raw_model = ModelFactory.create(config)
        model = ResilientBenchmarkModel(raw_model)
        extractor = MemoryExtractor(model=model)
        task_mgr = AsyncTaskManager(max_workers=4)

        t_start_flow = time.time()
        user_id = chat_store.create_user()
        conv_id = chat_store.create_conversation(user_id, "End-to-End Chat Session")

        ltm = LongTermMemory(
            chat_store=chat_store,
            user_id=user_id,
            vector_store=vector_store,
            embedding_model=embedding_model
        )

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

        user_messages = [
            "Hi! My name is Rakesh and I work as a Senior Backend Software Engineer.",
            "I prefer Python and FastAPI over Node.js or Java.",
            "My main goal this year is to crack a Principal AI Engineer interview.",
            "I live in Seattle, Washington.",
            "We decided to use ChromaDB for local vector embeddings storage.",
            "I plan to travel to Japan next fall.",
            "Can you remind me what programming language and web framework I prefer?",
            "What is my target career goal?",
            "Where do I live currently?",
            "What vector database did we pick?",
            "Where am I planning to go on vacation?",
            "Can you give me a summary of everything you remember about me?"
        ]

        turn_latencies_ms = []
        task_ids = []

        for turn_idx, msg in enumerate(user_messages[:num_turns], start=1):
            t0 = time.time()
            response = agent.chat(msg, async_processing=True)
            t1 = time.time()

            latency_ms = (t1 - t0) * 1000
            turn_latencies_ms.append(latency_ms)

            t_id = agent.get_last_task_id()
            if t_id:
                task_ids.append(t_id)

            print(f"Turn {turn_idx:2d}/{num_turns} -> Latency: {latency_ms:6.2f} ms | Task ID: {t_id}")

        task_mgr.wait_all(timeout=15.0)
        t_end_flow = time.time()
        total_e2e_duration_ms = (t_end_flow - t_start_flow) * 1000

        stored_memories = chat_store.get_memories(user_id)
        chroma_mems = vector_store.collection.get(where={"user_id": user_id})
        db_messages = chat_store.get_recent_messages(conv_id, limit=50)

        q_lat = calculate_quantiles(turn_latencies_ms)

        collector = BenchmarkResultCollector()
        collector.add_result("e2e_total_turns", num_turns, "count", "end_to_end", num_turns)
        collector.add_result("e2e_total_pipeline_duration", round(total_e2e_duration_ms, 2), "ms", "end_to_end", num_turns)
        collector.add_result("e2e_turn_latency_p50", q_lat["p50"], "ms", "end_to_end", num_turns)
        collector.add_result("e2e_turn_latency_p95", q_lat["p95"], "ms", "end_to_end", num_turns)
        collector.add_result("e2e_turn_latency_p99", q_lat["p99"], "ms", "end_to_end", num_turns)
        collector.add_result("e2e_turn_latency_mean", q_lat["mean"], "ms", "end_to_end", num_turns)
        collector.add_result("e2e_sqlite_memories_extracted", len(stored_memories), "count", "end_to_end", num_turns)
        collector.add_result("e2e_chroma_memories_indexed", len(chroma_mems.get("ids", [])), "count", "end_to_end", num_turns)
        collector.add_result("e2e_total_messages_persisted", len(db_messages), "count", "end_to_end", num_turns)
        collector.add_result("e2e_background_tasks_completed", len(task_ids), "count", "end_to_end", num_turns)

        print("\n--- END-TO-END PIPELINE SUMMARY ---")
        print(f"Total Turn Count          : {num_turns}")
        print(f"Total Pipeline Duration   : {total_e2e_duration_ms:.2f} ms")
        print(f"Turn Latency P50          : {q_lat['p50']} ms")
        print(f"Turn Latency P95          : {q_lat['p95']} ms")
        print(f"Turn Latency P99          : {q_lat['p99']} ms")
        print(f"Messages Persisted in DB  : {len(db_messages)}")
        print(f"Memories Extracted (SQLite): {len(stored_memories)}")
        print(f"Memories Indexed (Chroma) : {len(chroma_mems.get('ids', []))}")
        print(f"Background Tasks Spawned  : {len(task_ids)}")

        task_mgr.shutdown(wait=True)
        return collector.get_results()

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    run_e2e_benchmark()
