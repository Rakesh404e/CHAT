import json
import time
from typing import Optional
from .base import EmbeddingModel
from observability.logger import logger
from observability.metrics import metrics_collector
from utils.retry import retry_with_backoff

try:
    import boto3
    _HAS_BOTO3 = True
except ImportError:
    _HAS_BOTO3 = False


class BedrockEmbedding(EmbeddingModel):
    """
    Amazon Bedrock text embedding implementation (default: amazon.titan-embed-text-v1).
    """

    def __init__(
        self,
        model: str = "amazon.titan-embed-text-v1",
        region_name: str = "us-east-1",
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        aws_session_token: Optional[str] = None
    ):
        if not _HAS_BOTO3:
            raise ImportError(
                "boto3 package is required for Amazon Bedrock embeddings. Run 'pip install boto3'."
            )

        self.model = model
        self.region_name = region_name or "us-east-1"

        client_kwargs = {"region_name": self.region_name}
        if aws_access_key_id and aws_secret_access_key:
            client_kwargs["aws_access_key_id"] = aws_access_key_id
            client_kwargs["aws_secret_access_key"] = aws_secret_access_key
            if aws_session_token:
                client_kwargs["aws_session_token"] = aws_session_token

        self.client = boto3.client("bedrock-runtime", **client_kwargs)

    def embed(self, text: str, trace_id: str = None) -> list[float]:
        start_time = time.time()

        @retry_with_backoff(max_retries=3, initial_delay=0.2, trace_id=trace_id)
        def _embed():
            body = json.dumps({"inputText": text})
            response = self.client.invoke_model(
                modelId=self.model,
                body=body,
                contentType="application/json",
                accept="application/json"
            )
            response_body = json.loads(response["body"].read())
            return response_body["embedding"]

        try:
            vector = _embed()
            duration_ms = (time.time() - start_time) * 1000
            metrics_collector.record_embedding_call(duration_ms, success=True)
            return vector
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            metrics_collector.record_embedding_call(duration_ms, success=False)
            logger.error(
                f"Bedrock embedding generation failed: {e}",
                trace_id=trace_id,
                duration_ms=duration_ms,
                model=self.model
            )
            raise e
