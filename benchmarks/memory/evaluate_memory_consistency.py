import os
import sys
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
from benchmarks.common.benchmark_runner import BenchmarkResultCollector


def run_memory_consistency_benchmark():
    print("=" * 70)
    print("RUNNING PHASE 5 — MEMORY UPDATE / REVERSAL BENCHMARK")
    print("=" * 70)

    temp_dir = tempfile.mkdtemp(prefix="benchmark_consistency_")
    db_path = os.path.join(temp_dir, "test_consistency.db")
    chroma_path = os.path.join(temp_dir, "test_chroma")

    try:
        config = Config()
        db = Database(db_path=db_path)
        db.initialize()
        chat_store = ChatStore(db)

        user_id = 201
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO users (id) VALUES (?)", (user_id,))
        conn.commit()
        conn.close()

        vector_store = ChromaVectorStore(path=chroma_path, collection_name="test_consistency")
        embedding_model = EmbeddingFactory.create(config)

        ltm = LongTermMemory(
            chat_store=chat_store,
            user_id=user_id,
            vector_store=vector_store,
            embedding_model=embedding_model
        )

        test_cases = [
            ("preference", "programming_language", "User prefers Python for backend development", "User now prefers Go for backend development"),
            ("preference", "theme", "User prefers Light theme", "User now prefers Dark theme"),
            ("goal", "target_role", "Target role is Junior Engineer", "Target role is Senior AI Architect"),
            ("fact", "location", "User lives in New York", "User moved and lives in Seattle"),
            ("plan", "vacation", "Planning trip to Hawaii", "Changed plan to travel to Japan"),
            ("decision", "database", "Decided to use MySQL", "Reversed decision: now using PostgreSQL"),
            ("preference", "editor", "User uses Vim", "User switched to VS Code"),
            ("fact", "pet", "Has 1 cat", "Adopted a Golden Retriever dog"),
            ("goal", "salary", "Salary goal $100k", "Updated salary target to $200k"),
            ("plan", "framework", "Planning to learn Django", "Decided to master FastAPI instead")
        ]

        total_updates = len(test_cases)
        successful_updates = 0
        duplicate_conflicts = 0
        sync_failures = 0
        stale_memories = 0

        for m_type, key, initial_val, updated_val in test_cases:
            mem_id1 = ltm.add_or_update_memory(m_type, key, initial_val)
            mem_id2 = ltm.add_or_update_memory(m_type, key, updated_val)

            all_db_mems = chat_store.get_memories(user_id)
            matching_db = [m for m in all_db_mems if m["memory_type"] == m_type and m["key"] == key]

            if len(matching_db) > 1:
                duplicate_conflicts += len(matching_db) - 1

            if len(matching_db) == 1 and matching_db[0]["value"] == updated_val:
                successful_updates += 1
            else:
                stale_memories += 1

            try:
                chroma_results = vector_store.collection.get(where={"user_id": user_id, "key": key})
                chroma_ids = chroma_results.get("ids", [])
                chroma_docs = chroma_results.get("documents", [])

                if len(chroma_ids) != 1:
                    sync_failures += 1
                elif updated_val.lower() not in chroma_docs[0].lower():
                    sync_failures += 1
            except Exception as e:
                sync_failures += 1

        update_success_rate = round((successful_updates / total_updates) * 100, 2)
        stale_rate = round((stale_memories / total_updates) * 100, 2)

        collector = BenchmarkResultCollector()
        collector.add_result("total_memory_update_tests", total_updates, "count", "memory_consistency", total_updates)
        collector.add_result("memory_update_success_rate", update_success_rate, "percent", "memory_consistency", total_updates)
        collector.add_result("duplicate_conflicting_memories", duplicate_conflicts, "count", "memory_consistency", total_updates)
        collector.add_result("stale_memory_rate", stale_rate, "percent", "memory_consistency", total_updates)
        collector.add_result("dual_store_sync_failures", sync_failures, "count", "memory_consistency", total_updates)

        print("\n--- MEMORY UPDATE & REVERSAL RESULTS ---")
        print(f"Total Reversal Test Scenarios: {total_updates}")
        print(f"Update Success Rate: {update_success_rate}%")
        print(f"Duplicate Conflicting Memories: {duplicate_conflicts}")
        print(f"Stale Memory Rate: {stale_rate}%")
        print(f"SQLite / Chroma Synchronization Failures: {sync_failures}")

        return collector.get_results()

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    run_memory_consistency_benchmark()
