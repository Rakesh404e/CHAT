import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    def __init__(self):
        self.provider = os.getenv("PROVIDER", "groq").lower().strip()
        
        # Provider-specific API keys & credentials
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.aws_region = os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "us-east-1"))
        self.aws_session_token = os.getenv("AWS_SESSION_TOKEN")

        # Backward compatibility for code referencing config.api_key
        if self.provider == "groq":
            self.api_key = self.groq_api_key
        elif self.provider in ["bedrock", "amazon_bedrock", "aws_bedrock"]:
            self.api_key = self.aws_access_key_id
        else:
            self.api_key = self.openai_api_key

        # Model defaults per provider
        default_model = "gpt-4o-mini"
        if self.provider == "groq":
            default_model = "groq/compound-mini"
        elif self.provider in ["bedrock", "amazon_bedrock", "aws_bedrock"]:
            default_model = "anthropic.claude-3-5-sonnet-20240620-v1:0"



        self.model_name = (os.getenv("MODEL_NAME") or "").strip() or default_model

        # Embedding model settings
        self.embedding_provider = (os.getenv("EMBEDDING_PROVIDER") or "").lower().strip()
        default_embed = "text-embedding-3-small"
        if self.embedding_provider in ["bedrock", "amazon_bedrock", "aws_bedrock"] or (
            not self.embedding_provider and self.provider in ["bedrock", "amazon_bedrock", "aws_bedrock"]
        ):
            default_embed = "amazon.titan-embed-text-v1"
        self.embedding_model = (os.getenv("EMBEDDING_MODEL") or "").strip() or default_embed


        self.chroma_path = os.getenv("CHROMA_PATH", "./chroma_db")
        self.database_path = os.getenv("DATABASE_PATH", "./chatbot.db")
        self.temperature = float(os.getenv("TEMPERATURE", "0.7"))

        self.validate()

    def validate(self):
        if self.provider == "openai" and not self.openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY is missing. Please set OPENAI_API_KEY in your .env file."
            )
        elif self.provider == "groq" and not self.groq_api_key:
            raise ValueError(
                "GROQ_API_KEY is missing. Please set GROQ_API_KEY in your .env file."
            )
        elif self.provider in ["bedrock", "amazon_bedrock", "aws_bedrock"]:
            # Note: Bedrock can also authenticate via AWS SSO/IAM role/default credentials
            pass
