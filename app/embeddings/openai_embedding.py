import time
from openai import OpenAI
from .base import EmbeddingModel
from observability.logger import logger
from observability.metrics import metrics_collector
from utils.retry import retry_with_backoff


class OpenAIEmbedding(EmbeddingModel):

    def __init__(self, api_key, model):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def embed(self, text, trace_id: str = None):
        start_time = time.time()

        @retry_with_backoff(max_retries=3, initial_delay=0.2, trace_id=trace_id)
        def _embed():
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            return response.data[0].embedding

        try:
            vector = _embed()
            duration_ms = (time.time() - start_time) * 1000
            metrics_collector.record_embedding_call(duration_ms, success=True)
            return vector
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            metrics_collector.record_embedding_call(duration_ms, success=False)
            logger.error(f"Embedding generation failed: {e}", trace_id=trace_id, duration_ms=duration_ms)
            raise e