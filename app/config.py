import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    def __init__(self):
        self.provider = os.getenv("PROVIDER", "openai")
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model_name = os.getenv("MODEL_NAME", "gpt-4o-mini")
        self.temperature = float(os.getenv("TEMPERATURE", "0.7"))

        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY is missing"
            )