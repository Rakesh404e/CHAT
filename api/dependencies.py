import os
import sys

# Add app directory to sys.path
app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app"))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

from config import Config
from models.factory import ModelFactory
from memory.database import Database
from memory.chat_store import ChatStore
from memory.short_term import ShortTermMemory
from memory.long_term import LongTermMemory
from memory.extractor import MemoryExtractor
from vector_store.chroma_store import ChromaVectorStore
from embeddings.factory import EmbeddingFactory
from chatbot.agent import ChatAgent
from tasks.manager import task_manager


class AppServices:
    def __init__(self):
        self.config = Config()
        db_path = os.getenv("DATABASE_PATH", os.path.join(app_dir, "chatbot.db"))
        self.database = Database(db_path=db_path)
        self.database.initialize()
        self.chat_store = ChatStore(self.database)
        
        # Background Task Manager
        self.task_manager = task_manager

        # Models and Embeddings
        self.model = ModelFactory.create(self.config)
        chroma_path = os.getenv("CHROMA_PATH", os.path.join(app_dir, "chroma_db"))
        self.vector_store = ChromaVectorStore(path=chroma_path)
        self.embedding_model = EmbeddingFactory.create(self.config)
        self.extractor = MemoryExtractor(model=self.model)


    def get_long_term_memory(self, user_id: int) -> LongTermMemory:
        return LongTermMemory(
            chat_store=self.chat_store,
            user_id=user_id,
            vector_store=self.vector_store,
            embedding_model=self.embedding_model
        )

    def get_agent(self, user_id: int, conversation_id: int, async_processing: bool = True) -> ChatAgent:
        long_term_memory = self.get_long_term_memory(user_id)
        short_term_memory = ShortTermMemory()
        
        agent = ChatAgent(
            model=self.model,
            memory=short_term_memory,
            chat_store=self.chat_store,
            conversation_id=conversation_id,
            long_term_memory=long_term_memory,
            extractor=self.extractor,
            task_manager=self.task_manager,
            async_processing=async_processing
        )
        agent.load_context()
        return agent


# Global singleton instance
services = None


def get_services() -> AppServices:
    global services
    if services is None:
        services = AppServices()
    return services
