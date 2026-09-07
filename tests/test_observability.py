import os
import sys
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app')))

from app.observability.logger import StructuredLogger, logger
from app.observability.metrics import MetricsCollector
from app.utils.retry import retry_with_backoff
from app.memory.long_term import LongTermMemory
from app.memory.database import Database
from app.memory.chat_store import ChatStore
import tempfile
import shutil


class TestObservabilityAndReliability(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_obs.db")
        self.database = Database(db_path=self.db_path)
        self.database.initialize()
        self.chat_store = ChatStore(self.database)
        self.user_id = self.chat_store.create_user()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_structured_logger_format(self):
        obs_logger = StructuredLogger(name="TestLogger")
        trace_id = obs_logger.generate_trace_id()
        self.assertEqual(len(trace_id), 8)

        event_str = obs_logger._format_event("INFO", "Test message", trace_id=trace_id, duration_ms=12.34)
        self.assertIn("Test message", event_str)
        self.assertIn(trace_id, event_str)
        self.assertIn("12.34", event_str)

    def test_metrics_collector_recording(self):
        metrics = MetricsCollector()
        metrics.record_llm_call(150.0, success=True)
        metrics.record_llm_call(250.0, success=True)
        metrics.record_llm_call(0.0, success=False)

        metrics.record_embedding_call(50.0, success=True)
        metrics.record_memory_search(hit_count=3)
        metrics.record_memory_search(hit_count=0)
        metrics.record_memory_deletion(2)
        metrics.record_retry()
        metrics.record_task_started()
        metrics.record_task_event("memory_extraction", 80.0, success=True)
        metrics.record_task_started()
        metrics.record_task_event("summarization", 120.0, success=False)

        summary = metrics.get_metrics_summary()

        self.assertEqual(summary["llm"]["calls_total"], 3)
        self.assertEqual(summary["llm"]["errors_total"], 1)
        self.assertEqual(summary["llm"]["avg_latency_ms"], 200.0)

        self.assertEqual(summary["embedding"]["calls_total"], 1)
        self.assertEqual(summary["embedding"]["avg_latency_ms"], 50.0)

        self.assertEqual(summary["memory"]["searches_total"], 2)
        self.assertEqual(summary["memory"]["hits_total"], 1)
        self.assertEqual(summary["memory"]["hit_rate_pct"], 50.0)
        self.assertEqual(summary["memory"]["deletions_total"], 2)
        self.assertEqual(summary["reliability"]["retries_total"], 1)

        self.assertEqual(summary["background_tasks"]["total"], 2)
        self.assertEqual(summary["background_tasks"]["completed"], 1)
        self.assertEqual(summary["background_tasks"]["failed"], 1)
        self.assertEqual(summary["background_tasks"]["running"], 0)
        self.assertEqual(summary["background_tasks"]["avg_latency_ms"], 80.0)

    def test_retry_decorator_success(self):
        attempts = 0

        @retry_with_backoff(max_retries=3, initial_delay=0.01, backoff_factor=1.0)
        def flaky_function():
            nonlocal attempts
            attempts += 1
            if attempts < 2:
                raise ValueError("Transient error")
            return "Success"

        result = flaky_function()
        self.assertEqual(result, "Success")
        self.assertEqual(attempts, 2)

    def test_retry_decorator_fallback(self):
        def fallback_fn(*args, **kwargs):
            return "Fallback Response"

        @retry_with_backoff(max_retries=2, initial_delay=0.01, fallback_factory=fallback_fn)
        def failing_function():
            raise RuntimeError("Permanent failure")

        result = failing_function()
        self.assertEqual(result, "Fallback Response")

    def test_resilience_vector_store_failure(self):
        # Create LongTermMemory with a failing Mock Vector Store
        failing_vector_store = MagicMock()
        failing_vector_store.search.side_effect = Exception("ChromaDB connection timeout")
        mock_embedding = MagicMock()
        mock_embedding.embed.return_value = [0.1] * 1536

        ltm = LongTermMemory(
            chat_store=self.chat_store,
            user_id=self.user_id,
            vector_store=failing_vector_store,
            embedding_model=mock_embedding
        )

        # Add memory directly to SQLite
        self.chat_store.save_memory(self.user_id, "preference", "favorite_subject", "user loves DSA", None)

        # Search memories should not crash, but fallback gracefully to SQL keyword search
        results = ltm.search_memories("DSA", top_k=1)
        self.assertEqual(len(results), 1)
        self.assertIn("user loves DSA", results[0]["content"])


if __name__ == "__main__":
    unittest.main()
