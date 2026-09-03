import time
from openai import OpenAI
from .base import LLM
from observability.logger import logger
from observability.metrics import metrics_collector
from utils.retry import retry_with_backoff


class openAIModel(LLM):

    def __init__(self, api_key: str, model_name: str):
        self.client = OpenAI(api_key=api_key)
        self.model_name = model_name

    def generate(self, message: list, trace_id: str = None) -> str:
        start_time = time.time()

        @retry_with_backoff(max_retries=3, initial_delay=0.2, trace_id=trace_id)
        def _generate():
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=message
            )
            return response.choices[0].message.content

        try:
            result = _generate()
            duration_ms = (time.time() - start_time) * 1000
            metrics_collector.record_llm_call(duration_ms, success=True)
            logger.info("LLM generation successful", trace_id=trace_id, duration_ms=duration_ms, model=self.model_name)
            return result
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            metrics_collector.record_llm_call(duration_ms, success=False)
            logger.error(f"LLM generation failed: {e}", trace_id=trace_id, duration_ms=duration_ms)
            raise e
