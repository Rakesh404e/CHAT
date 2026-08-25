from openai import OpenAI
from .base import LLM


class openAIModel(LLM):

    def __init__(self, api_key: str, model_name: str):
        self.client = OpenAI(api_key=api_key)
        self.model_name = model_name

    def generate(self, message: str) -> str:
        response = self.client.responses.create(
            model=self.model_name,
            input=message
        )

        return response.output_text