from .openai_model import openAIModel


class ModelFactory:

    @staticmethod
    def create(config):

        if config.provider == "openai":
            return openAIModel(
                api_key=config.api_key,
                model_name=config.model_name
            )

        raise ValueError(
            f"Unsupported provider: {config.provider}"
        )