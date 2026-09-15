import os
import sys
import unittest
from unittest.mock import MagicMock, patch

app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app"))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

from config import Config
from models.factory import ModelFactory
from models.groq_model import GroqModel
from models.bedrock_model import BedrockModel
from models.openai_model import openAIModel
from embeddings.factory import EmbeddingFactory
from embeddings.fallback_embedding import LocalFallbackEmbedding
from embeddings.openai_embedding import OpenAIEmbedding
from embeddings.bedrock_embedding import BedrockEmbedding


class TestModelProviders(unittest.TestCase):

    def test_config_groq_defaults(self):
        with patch.dict(os.environ, {"PROVIDER": "groq", "GROQ_API_KEY": "gsk_test123", "MODEL_NAME": ""}):
            cfg = Config()
            self.assertEqual(cfg.provider, "groq")
            self.assertEqual(cfg.groq_api_key, "gsk_test123")
            self.assertEqual(cfg.api_key, "gsk_test123")
            self.assertEqual(cfg.model_name, "groq/compound-mini")



    def test_config_groq_missing_key_raises_error(self):
        with patch.dict(os.environ, {"PROVIDER": "groq", "GROQ_API_KEY": ""}):
            with self.assertRaises(ValueError) as ctx:
                Config()
            self.assertIn("GROQ_API_KEY is missing", str(ctx.exception))

    def test_config_bedrock_defaults(self):
        with patch.dict(os.environ, {"PROVIDER": "bedrock", "MODEL_NAME": ""}):
            cfg = Config()
            self.assertEqual(cfg.provider, "bedrock")
            self.assertEqual(cfg.model_name, "anthropic.claude-3-5-sonnet-20240620-v1:0")
            self.assertEqual(cfg.embedding_model, "amazon.titan-embed-text-v1")

    def test_model_factory_creates_groq(self):
        cfg = MagicMock()
        cfg.provider = "groq"
        cfg.groq_api_key = "gsk_test123"
        cfg.model_name = "llama-3.3-70b-versatile"
        cfg.temperature = 0.7

        model = ModelFactory.create(cfg)
        self.assertIsInstance(model, GroqModel)
        self.assertEqual(model.model_name, "llama-3.3-70b-versatile")

    def test_model_factory_creates_bedrock(self):
        cfg = MagicMock()
        cfg.provider = "bedrock"
        cfg.model_name = "anthropic.claude-3-5-sonnet-20240620-v1:0"
        cfg.aws_region = "us-east-1"
        cfg.aws_access_key_id = "test_key"
        cfg.aws_secret_access_key = "test_secret"
        cfg.aws_session_token = None
        cfg.temperature = 0.7

        model = ModelFactory.create(cfg)
        self.assertIsInstance(model, BedrockModel)
        self.assertEqual(model.model_name, "anthropic.claude-3-5-sonnet-20240620-v1:0")

    def test_model_factory_creates_openai(self):
        cfg = MagicMock()
        cfg.provider = "openai"
        cfg.openai_api_key = "sk-test123"
        cfg.model_name = "gpt-4o-mini"

        model = ModelFactory.create(cfg)
        self.assertIsInstance(model, openAIModel)

    def test_groq_model_generate_mock(self):
        model = GroqModel(api_key="gsk_fake", model_name="llama-3.3-70b-versatile")
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "Groq hello answer"
        mock_response.choices = [mock_choice]

        model.client.chat.completions.create = MagicMock(return_value=mock_response)
        result = model.generate([{"role": "user", "content": "Hello Groq"}])

        self.assertEqual(result, "Groq hello answer")
        model.client.chat.completions.create.assert_called_once()

    def test_bedrock_model_generate_mock(self):
        model = BedrockModel(
            model_name="anthropic.claude-3-5-sonnet-20240620-v1:0",
            region_name="us-east-1",
            aws_access_key_id="mock_id",
            aws_secret_access_key="mock_secret"
        )
        mock_converse_resp = {
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [{"text": "Bedrock response output"}]
                }
            }
        }
        model.client.converse = MagicMock(return_value=mock_converse_resp)

        messages = [
            {"role": "system", "content": "Be concise"},
            {"role": "user", "content": "Hello Bedrock"}
        ]
        result = model.generate(messages)
        self.assertEqual(result, "Bedrock response output")
        model.client.converse.assert_called_once()

    def test_local_fallback_embedding(self):
        embedder = LocalFallbackEmbedding(dimension=1536)
        vec1 = embedder.embed("Python programming tutorial")
        vec2 = embedder.embed("Python programming tutorial")
        vec3 = embedder.embed("Cooking recipes for dinner")

        self.assertEqual(len(vec1), 1536)
        # Deterministic
        self.assertEqual(vec1, vec2)
        # Distinct texts produce different vectors
        self.assertNotEqual(vec1, vec3)

    def test_embedding_factory_fallback(self):
        cfg = MagicMock()
        cfg.embedding_provider = ""
        cfg.openai_api_key = None
        cfg.aws_access_key_id = None
        cfg.provider = "groq"

        embedder = EmbeddingFactory.create(cfg)
        self.assertIsInstance(embedder, LocalFallbackEmbedding)


if __name__ == "__main__":
    unittest.main()
