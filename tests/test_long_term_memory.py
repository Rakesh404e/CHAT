import os
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app')))

from app.memory.database import Database
from app.memory.chat_store import ChatStore
from app.memory.long_term import LongTermMemory
from app.memory.extractor import MemoryExtractor, Memory, MemoryType
from app.vector_store.chroma_store import ChromaVectorStore



class MockEmbeddingModel:
    def embed(self, text: str):
        # Return simple deterministic pseudo-vector based on length
        val = float(len(text) % 10)
        return [val] * 1536


class TestLongTermMemory(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_chatbot.db")
        self.chroma_path = os.path.join(self.temp_dir, "test_chroma")

        self.database = Database(db_path=self.db_path)
        self.database.initialize()
        self.chat_store = ChatStore(self.database)
        self.user_id = self.chat_store.create_user()

        self.vector_store = ChromaVectorStore(path=self.chroma_path, collection_name="test_memories")
        self.embedding_model = MockEmbeddingModel()

        self.ltm = LongTermMemory(
            chat_store=self.chat_store,
            user_id=self.user_id,
            vector_store=self.vector_store,
            embedding_model=self.embedding_model
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_add_and_retrieve_memory(self):
        # 1. Add preference
        mem_id = self.ltm.add_or_update_memory(
            memory_type="preference",
            key="favorite_subject",
            value="user loves DSA"
        )
        self.assertIsNotNone(mem_id)

        # 2. Check SQLite persistent storage
        memories = self.chat_store.get_memories(self.user_id)
        self.assertEqual(len(memories), 1)
        self.assertEqual(memories[0]["key"], "favorite_subject")
        self.assertEqual(memories[0]["value"], "user loves DSA")

        # 3. Check Vector Store search
        search_results = self.ltm.search_memories("DSA", top_k=1)
        self.assertEqual(len(search_results), 1)
        self.assertIn("user loves DSA", search_results[0]["content"])

    def test_memory_reversal_and_update(self):
        # 1. User initially loves DSA
        mem_id1 = self.ltm.add_or_update_memory(
            memory_type="preference",
            key="favorite_subject",
            value="user loves DSA"
        )

        # 2. User reverses preference: hates DSA, prefers Machine Learning
        mem_id2 = self.ltm.add_or_update_memory(
            memory_type="preference",
            key="favorite_subject",
            value="user prefers Machine Learning over DSA"
        )

        # Ensure ID remains same (updated in-place)
        self.assertEqual(mem_id1, mem_id2)

        # Check SQLite has updated value and still 1 entry
        memories = self.chat_store.get_memories(self.user_id)
        self.assertEqual(len(memories), 1)
        self.assertEqual(memories[0]["value"], "user prefers Machine Learning over DSA")

        # Check Vector Store search returns updated memory
        search_results = self.ltm.search_memories("Machine Learning", top_k=1)
        self.assertEqual(len(search_results), 1)
        self.assertIn("Machine Learning", search_results[0]["content"])

    def test_memory_extractor_parsing(self):
        mock_llm = MagicMock()
        mock_llm.generate.return_value = '''
        ```json
        {
            "memories": [
                {
                    "memory_type": "preference",
                    "key": "favorite_subject",
                    "value": "user loves DSA",
                    "scope": null
                }
            ]
        }
        ```
        '''

        extractor = MemoryExtractor(model=mock_llm)
        memories = extractor.extract("i love dsa")

        self.assertEqual(len(memories), 1)
        self.assertEqual(memories[0].memory_type, MemoryType.PREFERENCE)
        self.assertEqual(memories[0].key, "favorite_subject")
        self.assertEqual(memories[0].value, "user loves DSA")

    def test_delete_memory_by_id(self):
        mem_id = self.ltm.add_or_update_memory("fact", "location", "lives in New York")
        self.assertEqual(len(self.chat_store.get_memories(self.user_id)), 1)

        self.ltm.delete_memory(mem_id)
        self.assertEqual(len(self.chat_store.get_memories(self.user_id)), 0)
        search_res = self.ltm.search_memories("New York", top_k=1)
        self.assertEqual(len(search_res), 0)

    def test_delete_memory_by_key(self):
        self.ltm.add_or_update_memory("fact", "location", "lives in New York")
        self.ltm.add_or_update_memory("goal", "target_role", "wants to be SDE")

        self.assertEqual(len(self.chat_store.get_memories(self.user_id)), 2)

        deleted_count = self.ltm.delete_memory_by_key("fact", "location")
        self.assertEqual(deleted_count, 1)

        memories = self.chat_store.get_memories(self.user_id)
        self.assertEqual(len(memories), 1)
        self.assertEqual(memories[0]["key"], "target_role")

        search_res = self.ltm.search_memories("location New York", top_k=5)
        self.assertTrue(all(item["metadata"]["key"] != "location" for item in search_res))

    def test_delete_all_memories(self):
        self.ltm.add_or_update_memory("preference", "fav_color", "blue")
        self.ltm.add_or_update_memory("fact", "city", "Tokyo")

        self.assertEqual(len(self.chat_store.get_memories(self.user_id)), 2)

        count = self.ltm.delete_all_memories()
        self.assertEqual(count, 2)
        self.assertEqual(len(self.chat_store.get_memories(self.user_id)), 0)

    def test_hybrid_retrieval_and_rrf(self):
        self.ltm.add_or_update_memory("preference", "favorite_language", "user loves Python")
        self.ltm.add_or_update_memory("goal", "target_role", "user aims for Backend Engineer")
        self.ltm.add_or_update_memory("fact", "city", "lives in San Francisco")

        results = self.ltm.search_memories("python backend engineer", top_k=2)
        self.assertGreater(len(results), 0)
        self.assertIn("score", results[0])
        # Top result should contain either python or backend engineer
        top_content = results[0]["content"].lower()
        self.assertTrue("python" in top_content or "backend" in top_content)

    def test_memory_extractor_deletion_parsing(self):
        mock_llm = MagicMock()
        mock_llm.generate.return_value = '''
        ```json
        {
            "memories": [
                {
                    "action": "delete",
                    "memory_type": "fact",
                    "key": "location",
                    "value": "",
                    "scope": null
                },
                {
                    "action": "delete_all",
                    "memory_type": "fact",
                    "key": "",
                    "value": "",
                    "scope": null
                }
            ]
        }
        ```
        '''

        extractor = MemoryExtractor(model=mock_llm)
        memories = extractor.extract("Forget my location and wipe all memories")

        self.assertEqual(len(memories), 2)
        self.assertEqual(memories[0].action.value, "delete")
        self.assertEqual(memories[0].key, "location")
        self.assertEqual(memories[1].action.value, "delete_all")


if __name__ == "__main__":
    unittest.main()

