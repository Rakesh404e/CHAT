import hashlib
import math
import time
from .base import EmbeddingModel
from observability.logger import logger
from observability.metrics import metrics_collector


class LocalFallbackEmbedding(EmbeddingModel):
    """
    Deterministic local embedding model used when no external embedding API key
    (OpenAI or AWS Bedrock) is configured (e.g. running purely with Groq).
    Produces normalized 1536-dimensional vectors using word hashing and character n-grams.
    Ensures vector store (ChromaDB) operations work offline without API dependencies.
    """

    def __init__(self, dimension: int = 1536):
        self.dimension = dimension

    def embed(self, text: str, trace_id: str = None) -> list[float]:
        start_time = time.time()
        
        vec = [0.0] * self.dimension
        if not text:
            duration_ms = (time.time() - start_time) * 1000
            metrics_collector.record_embedding_call(duration_ms, success=True)
            return vec

        # Tokenize words and character n-grams
        tokens = text.lower().split()
        for token in tokens:
            # Word hash
            h_int = int(hashlib.md5(token.encode('utf-8')).hexdigest(), 16)
            idx = h_int % self.dimension
            sign = 1.0 if ((h_int >> 16) & 1) == 1 else -1.0
            vec[idx] += sign * 2.0

            # Character 3-grams for substring similarity
            if len(token) >= 3:
                for i in range(len(token) - 2):
                    ngram = token[i:i+3]
                    h_ng = int(hashlib.sha256(ngram.encode('utf-8')).hexdigest()[:8], 16)
                    idx_ng = h_ng % self.dimension
                    vec[idx_ng] += 1.0

        # L2 normalize
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0.0:
            vec = [x / norm for x in vec]

        duration_ms = (time.time() - start_time) * 1000
        metrics_collector.record_embedding_call(duration_ms, success=True)
        return vec
