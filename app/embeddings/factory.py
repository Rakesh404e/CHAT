from .openai_embedding import OpenAIEmbedding
from .bedrock_embedding import BedrockEmbedding
from .fallback_embedding import LocalFallbackEmbedding
from observability.logger import logger


class EmbeddingFactory:
    """
    Factory for instantiating text embedding models based on application configuration.
    Supports OpenAI, Amazon Bedrock (Titan), and offline LocalFallback embeddings.
    """

    @staticmethod
    def create(config):
        embedding_provider = getattr(config, "embedding_provider", "").lower().strip()
        openai_key = getattr(config, "openai_api_key", None)
        aws_key = getattr(config, "aws_access_key_id", None)
        provider = (getattr(config, "provider", "") or "").lower().strip()

        # 1. Explicit or default Bedrock embeddings
        if embedding_provider in ["bedrock", "amazon_bedrock", "aws_bedrock"] or (
            not embedding_provider and provider in ["bedrock", "amazon_bedrock", "aws_bedrock"] and aws_key
        ):
            try:
                return BedrockEmbedding(
                    model=config.embedding_model or "amazon.titan-embed-text-v1",
                    region_name=getattr(config, "aws_region", "us-east-1"),
                    aws_access_key_id=aws_key,
                    aws_secret_access_key=getattr(config, "aws_secret_access_key", None),
                    aws_session_token=getattr(config, "aws_session_token", None)
                )
            except Exception as e:
                logger.warning(f"Could not initialize BedrockEmbedding: {e}. Falling back to local embedding.")
                return LocalFallbackEmbedding()

        # 2. OpenAI embeddings if configured
        if embedding_provider == "openai" or (not embedding_provider and openai_key):
            if openai_key:
                return OpenAIEmbedding(
                    api_key=openai_key,
                    model=config.embedding_model or "text-embedding-3-small"
                )
            else:
                logger.warning("OPENAI_API_KEY is not configured for OpenAI embeddings. Falling back to local embedding.")
                return LocalFallbackEmbedding()

        # 3. Fallback deterministic local embedding (e.g. Pure Groq mode)
        logger.info("Using LocalFallbackEmbedding for vector store (running without external embedding API key).")
        return LocalFallbackEmbedding()
