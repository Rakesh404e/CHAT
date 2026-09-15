from .openai_model import openAIModel
from .groq_model import GroqModel
from .bedrock_model import BedrockModel


class ModelFactory:

    @staticmethod
    def create(config):
        provider = (config.provider or "groq").lower().strip()

        if provider == "openai":
            api_key = getattr(config, "openai_api_key", None) or getattr(config, "api_key", None)
            return openAIModel(
                api_key=api_key,
                model_name=config.model_name
            )

        elif provider == "groq":
            api_key = getattr(config, "groq_api_key", None) or getattr(config, "api_key", None)
            temperature = getattr(config, "temperature", 0.7)
            return GroqModel(
                api_key=api_key,
                model_name=config.model_name,
                temperature=temperature
            )

        elif provider in ["bedrock", "amazon_bedrock", "aws_bedrock"]:
            return BedrockModel(
                model_name=config.model_name,
                region_name=getattr(config, "aws_region", "us-east-1"),
                aws_access_key_id=getattr(config, "aws_access_key_id", None),
                aws_secret_access_key=getattr(config, "aws_secret_access_key", None),
                aws_session_token=getattr(config, "aws_session_token", None),
                temperature=getattr(config, "temperature", 0.7)
            )

        raise ValueError(
            f"Unsupported provider: '{config.provider}'. Supported providers: 'groq', 'openai', 'bedrock'."
        )