import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    def __init__(self):
        self.provider = os.getenv("PROVIDER", "openai")
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model_name = os.getenv("MODEL_NAME", "gpt-4o-mini")
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        self.chroma_path = os.getenv("CHROMA_PATH", "./chroma_db")
        self.database_path = os.getenv("DATABASE_PATH", "./chatbot.db")
        self.temperature = float(os.getenv("TEMPERATURE", "0.7"))

        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY is missing"
            )