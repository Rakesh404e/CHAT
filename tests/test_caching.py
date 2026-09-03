import os
import sys
import time
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app')))

from app.caching.cache_store import TTLCache
from app.caching.embedding_cache import CachedEmbeddingModel
from app.caching.memory_cache import MemoryQueryCache
from app.memory.long_term import LongTermMemory
from app.memory.database import Database
from app.memory.chat_store import ChatStore
import tempfile
import shutil


class TestCachingArchitecture(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_cache.db")
        self.database = Database(db_path=self.db_path)
        self.database.initialize()
        self.chat_store = ChatStore(self.database)
        self.user_id = self.chat_store.create_user()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_ttl_cache_eviction_and_expiration(self):
        cache = TTLCache(maxsize=2, ttl_seconds=0.2)

        cache.set("k1", "v1")
        cache.set("k2", "v2")
        self.assertEqual(cache.get("k1"), "v1")
        self.assertEqual(cache.get("k2"), "v2")

        # Over capacity eviction (FIFO)
        cache.set("k3", "v3")
        self.assertIsNone(cache.get("k1"))  # evicted
        self.assertEqual(cache.get("k3"), "v3")

        # TTL Expiration test
        time.sleep(0.3)
        self.assertIsNone(cache.get("k2"))
        self.assertIsNone(cache.get("k3"))

    def test_ttl_cache_prefix_invalidation(self):
        cache = TTLCache(maxsize=10, ttl_seconds=60)
        cache.set("user:1:pref", "val1")
        cache.set("user:1:goal", "val2")
        cache.set("user:2:pref", "val3")

        count = cache.invalidate_prefix("user:1:")
        self.assertEqual(count, 2)
        self.assertIsNone(cache.get("user:1:pref"))
        self.assertIsNone(cache.get("user:1:goal"))
        self.assertEqual(cache.get("user:2:pref"), "val3")

    def test_cached_embedding_model(self):
        mock_embedding_api = MagicMock()
        mock_embedding_api.embed.return_value = [0.123] * 1536

        cached_model = CachedEmbeddingModel(embedding_model=mock_embedding_api, maxsize=100, ttl_seconds=60)

        # First call -> embedding API called
        vec1 = cached_model.embed("I love Python")
        self.assertEqual(len(vec1), 1536)
        self.assertEqual(mock_embedding_api.embed.call_count, 1)

        # Second call with identical text -> cache HIT, no extra API call
        vec2 = cached_model.embed("I love Python")
        self.assertEqual(vec1, vec2)
        self.assertEqual(mock_embedding_api.embed.call_count, 1)

        stats = cached_model.get_cache_stats()
        self.assertEqual(stats["hits"], 1)
        self.assertEqual(stats["misses"], 1)

    def test_memory_search_caching_and_invalidation(self):
        query_cache = MemoryQueryCache()
        ltm = LongTermMemory(
            chat_store=self.chat_store,
            user_id=self.user_id,
            query_cache=query_cache
        )

        ltm.add_or_update_memory("preference", "fav_lang", "user loves Python")

        # 1st Search -> cache miss, populates query cache
        results1 = ltm.search_memories("Python", top_k=1)
        self.assertEqual(len(results1), 1)

        # 2nd Search -> cache hit
        results2 = ltm.search_memories("Python", top_k=1)
        self.assertEqual(results1, results2)
        self.assertGreater(query_cache.get_stats()["hits"], 0)

        # Update memory -> invalidates user query cache
        ltm.add_or_update_memory("preference", "fav_lang", "user loves Rust over Python")
        self.assertIsNone(query_cache.get(self.user_id, "Python", 1, 0.0))

        # Re-query fetches updated memory
        results3 = ltm.search_memories("Python", top_k=1)
        self.assertIn("user loves Rust over Python", results3[0]["content"])


if __name__ == "__main__":
    unittest.main()
