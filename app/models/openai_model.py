from openai import OpenAI
from .base import LLM


class openAIModel(LLM):

    def __init__(self, api_key: str, model_name: str):
        self.client = OpenAI(api_key=api_key)
        self.model_name = model_name

    def generate(self, message: list) -> str:
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=message
        )

        return response.choices[0].message.content