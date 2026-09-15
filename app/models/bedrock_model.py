import time
from typing import Optional
from .base import LLM
from observability.logger import logger
from observability.metrics import metrics_collector
from utils.retry import retry_with_backoff

try:
    import boto3
    _HAS_BOTO3 = True
except ImportError:
    _HAS_BOTO3 = False


class BedrockModel(LLM):
    """
    Amazon Bedrock LLM implementation using AWS Bedrock Runtime Converse API.
    Supports Anthropic Claude, Meta Llama, Amazon Nova, Mistral, and Amazon Titan models.
    """

    def __init__(
        self,
        model_name: str = "anthropic.claude-3-5-sonnet-20240620-v1:0",
        region_name: str = "us-east-1",
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        aws_session_token: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ):
        if not _HAS_BOTO3:
            raise ImportError(
                "boto3 package is required for Amazon Bedrock. Please run 'pip install boto3'."
            )

        self.model_name = model_name
        self.region_name = region_name or "us-east-1"
        self.temperature = temperature
        self.max_tokens = max_tokens

        client_kwargs = {"region_name": self.region_name}
        if aws_access_key_id and aws_secret_access_key:
            client_kwargs["aws_access_key_id"] = aws_access_key_id
            client_kwargs["aws_secret_access_key"] = aws_secret_access_key
            if aws_session_token:
                client_kwargs["aws_session_token"] = aws_session_token

        self.client = boto3.client("bedrock-runtime", **client_kwargs)

    def _format_messages_for_converse(self, raw_messages: list):
        """
        Adapts standard OpenAI-style message dictionaries to the Amazon Bedrock Converse API format.
        - System messages are extracted into a separate system array.
        - Consecutive messages with identical roles are merged.
        - Sequences are guaranteed to start with a 'user' turn.
        """
        system_prompts = []
        converse_messages = []

        for msg in raw_messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if not isinstance(content, str):
                content = str(content)

            if role == "system":
                if content.strip():
                    system_prompts.append({"text": content})
            elif role in ["user", "assistant"]:
                if not content.strip():
                    continue

                # Merge consecutive messages with the same role
                if converse_messages and converse_messages[-1]["role"] == role:
                    converse_messages[-1]["content"].append({"text": content})
                else:
                    converse_messages.append({
                        "role": role,
                        "content": [{"text": content}]
                    })

        # Bedrock requires the conversation to begin with a user turn
        if not converse_messages:
            converse_messages = [{"role": "user", "content": [{"text": "Hello"}]}]
        elif converse_messages[0]["role"] != "user":
            converse_messages.insert(0, {"role": "user", "content": [{"text": "Context overview:"}]})

        return system_prompts, converse_messages

    def generate(self, message: list, trace_id: str = None) -> str:
        start_time = time.time()
        system_prompts, converse_messages = self._format_messages_for_converse(message)

        @retry_with_backoff(max_retries=3, initial_delay=0.2, trace_id=trace_id)
        def _generate():
            kwargs = {
                "modelId": self.model_name,
                "messages": converse_messages,
                "inferenceConfig": {
                    "temperature": self.temperature,
                    "maxTokens": self.max_tokens
                }
            }
            if system_prompts:
                kwargs["system"] = system_prompts

            response = self.client.converse(**kwargs)
            output_msg = response.get("output", {}).get("message", {})
            parts = output_msg.get("content", [])
            text_chunks = [part.get("text", "") for part in parts if "text" in part]
            return "".join(text_chunks)

        try:
            result = _generate()
            duration_ms = (time.time() - start_time) * 1000
            metrics_collector.record_llm_call(duration_ms, success=True)
            logger.info(
                "Amazon Bedrock LLM generation successful",
                trace_id=trace_id,
                duration_ms=duration_ms,
                model=self.model_name
            )
            return result
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            metrics_collector.record_llm_call(duration_ms, success=False)
            logger.error(
                f"Amazon Bedrock LLM generation failed: {e}",
                trace_id=trace_id,
                duration_ms=duration_ms,
                model=self.model_name
            )
            raise e
