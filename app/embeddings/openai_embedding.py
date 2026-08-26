from openai import OpenAI

from .base import EmbeddingModel


class OpenAIEmbedding(EmbeddingModel):

    def __init__(self, api_key, model):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def embed(self, text):

        response = self.client.embeddings.create(
            model=self.model,
            input=text
        )

        return response.data[0].embedding