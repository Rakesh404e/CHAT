import os
import sys
import time
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app')))

from app.tasks.manager import AsyncTaskManager, TaskStatus, TaskType
from app.memory.database import Database
from app.memory.chat_store import ChatStore
from app.memory.short_term import ShortTermMemory
from app.memory.long_term import LongTermMemory
from app.chatbot.agent import ChatAgent
from app.observability.metrics import MetricsCollector


class MockEmbeddingModel:
    def embed(self, text: str):
        val = float(len(text) % 10)
        return [val] * 1536


class TestAsyncTasksAndBackgroundProcessing(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_tasks.db")
        self.database = Database(db_path=self.db_path)
        self.database.initialize()
        self.chat_store = ChatStore(self.database)
        self.user_id = self.chat_store.create_user()
        self.conversation_id = self.chat_store.create_conversation(self.user_id, "Async Test Session")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_task_manager_lifecycle_success(self):
        manager = AsyncTaskManager(max_workers=2)

        def sample_job(x, y):
            time.sleep(0.05)
            return x + y

        task_id = manager.submit(
            TaskType.GENERAL,
            sample_job,
            10,
            20,
            metadata={"user_id": self.user_id}
        )
        self.assertTrue(task_id.startswith("task_"))

        # Wait for completion
        record = manager.wait_for_task(task_id, timeout=2.0)
        self.assertIsNotNone(record)
        self.assertEqual(record.status, TaskStatus.COMPLETED)
        self.assertEqual(record.result, 30)
        self.assertIsNone(record.error)
        self.assertIsNotNone(record.duration_ms)
        self.assertGreater(record.duration_ms, 0)

        # List tasks
        user_tasks = manager.list_tasks(user_id=self.user_id)
        self.assertEqual(len(user_tasks), 1)
        self.assertEqual(user_tasks[0].task_id, task_id)

        manager.shutdown(wait=True)

    def test_task_manager_lifecycle_failure(self):
        manager = AsyncTaskManager(max_workers=2)

        def failing_job():
            raise ValueError("Deliberate background task error")

        task_id = manager.submit(
            TaskType.MEMORY_EXTRACTION,
            failing_job,
            metadata={"user_id": self.user_id}
        )

        record = manager.wait_for_task(task_id, timeout=2.0)
        self.assertIsNotNone(record)
        self.assertEqual(record.status, TaskStatus.FAILED)
        self.assertIn("Deliberate background task error", record.error)
        self.assertIsNone(record.result)

        manager.shutdown(wait=True)

    def test_task_manager_max_history_eviction(self):
        manager = AsyncTaskManager(max_workers=2, max_history=3)

        for i in range(5):
            t_id = manager.submit(TaskType.GENERAL, lambda n: n * 2, i)
            manager.wait_for_task(t_id, timeout=1.0)

        tasks = manager.list_tasks(limit=10)
        # Should be bounded by max_history
        self.assertLessEqual(len(tasks), 3)

        manager.shutdown(wait=True)

    def test_chat_agent_async_memory_extraction(self):
        # Set up mock LLM and extractor
        mock_model = MagicMock()
        mock_model.generate.return_value = "I noted that you love Python and FastAPI!"

        # Mock extractor returning a structured preference memory
        mock_extractor = MagicMock()
        mock_mem = MagicMock()
        mock_mem.memory_type.value = "preference"
        mock_mem.key = "favorite_language"
        mock_mem.value = "user loves Python and FastAPI"
        mock_mem.action = "add_or_update"
        mock_mem.scope = "general"
        mock_extractor.extract.return_value = [mock_mem]

        # Mock vector store
        mock_vector_store = MagicMock()
        mock_vector_store.search.return_value = []

        ltm = LongTermMemory(
            chat_store=self.chat_store,
            user_id=self.user_id,
            vector_store=mock_vector_store,
            embedding_model=MockEmbeddingModel()
        )

        task_manager = AsyncTaskManager(max_workers=2)
        memory = ShortTermMemory()

        agent = ChatAgent(
            model=mock_model,
            memory=memory,
            chat_store=self.chat_store,
            conversation_id=self.conversation_id,
            long_term_memory=ltm,
            extractor=mock_extractor,
            task_manager=task_manager,
            async_processing=True
        )

        # 1. Chat call in async mode
        response = agent.chat("I love Python and FastAPI!")
        self.assertEqual(response, "I noted that you love Python and FastAPI!")

        # 2. Verify task ID was assigned
        task_id = agent.get_last_task_id()
        self.assertIsNotNone(task_id)

        # 3. Wait for background task to complete
        success = agent.wait_for_background_tasks(timeout=3.0)
        self.assertTrue(success)

        # 4. Verify memories were persisted to SQLite by the background worker
        memories = self.chat_store.get_memories(self.user_id)
        self.assertEqual(len(memories), 1)
        self.assertEqual(memories[0]["key"], "favorite_language")
        self.assertEqual(memories[0]["value"], "user loves Python and FastAPI")

        # 5. Verify vector store update was called by background worker
        self.assertTrue(mock_vector_store.update.called or mock_vector_store.add.called)

        task_manager.shutdown(wait=True)

    def test_chat_agent_sync_mode_fallback(self):
        mock_model = MagicMock()
        mock_model.generate.return_value = "Sync answer"

        mock_extractor = MagicMock()
        mock_extractor.extract.return_value = []

        agent = ChatAgent(
            model=mock_model,
            memory=ShortTermMemory(),
            chat_store=self.chat_store,
            conversation_id=self.conversation_id,
            long_term_memory=None,
            extractor=mock_extractor,
            async_processing=False
        )

        response = agent.chat("Hello!", async_processing=False)
        self.assertEqual(response, "Sync answer")
        self.assertIsNone(agent.get_last_task_id())


if __name__ == "__main__":
    unittest.main()
