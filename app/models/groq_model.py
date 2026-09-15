import time
from .base import LLM
from observability.logger import logger
from observability.metrics import metrics_collector
from utils.retry import retry_with_backoff

try:
    from groq import Groq
    _HAS_GROQ_PKG = True
except ImportError:
    _HAS_GROQ_PKG = False
    from openai import OpenAI


class GroqModel(LLM):
    """
    Groq LLM implementation providing ultra-fast inference with Groq models.
    Supports official groq SDK with automatic fallback to OpenAI-compatible Groq API endpoint.
    """

    def __init__(self, api_key: str, model_name: str = "groq/compound-mini", temperature: float = 0.7):
        self.api_key = api_key
        self.model_name = model_name
        self.temperature = temperature



        if _HAS_GROQ_PKG:
            self.client = Groq(api_key=api_key)
        else:
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://api.groq.com/openai/v1"
            )

    def generate(self, message: list, trace_id: str = None) -> str:
        start_time = time.time()

        # Groq API requires that the last message role must be 'user'
        clean_messages = []
        if isinstance(message, list):
            for m in message:
                if isinstance(m, dict):
                    clean_messages.append({"role": m.get("role", "user"), "content": m.get("content", "")})
                else:
                    clean_messages.append({"role": "user", "content": str(m)})

            if not clean_messages:
                clean_messages = [{"role": "user", "content": ""}]
            elif clean_messages[-1]["role"] != "user":
                if len(clean_messages) == 1 and clean_messages[0]["role"] == "system":
                    clean_messages[0]["role"] = "user"
                else:
                    clean_messages.append({"role": "user", "content": "Please continue and summarize or respond."})
        elif isinstance(message, str):
            clean_messages = [{"role": "user", "content": message}]
        else:
            clean_messages = [{"role": "user", "content": str(message)}]

        @retry_with_backoff(max_retries=3, initial_delay=0.2, trace_id=trace_id)
        def _generate():
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=clean_messages,
                temperature=self.temperature
            )
            return response.choices[0].message.content

        try:
            result = _generate()
            duration_ms = (time.time() - start_time) * 1000
            metrics_collector.record_llm_call(duration_ms, success=True)
            logger.info(
                "Groq LLM generation successful",
                trace_id=trace_id,
                duration_ms=duration_ms,
                model=self.model_name
            )
            return result
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            metrics_collector.record_llm_call(duration_ms, success=False)
            logger.error(
                f"Groq LLM generation failed: {e}",
                trace_id=trace_id,
                duration_ms=duration_ms,
                model=self.model_name
            )
            raise e
