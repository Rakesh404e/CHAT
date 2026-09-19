import os
import sys
import math
from pathlib import Path

workspace_dir = Path(__file__).resolve().parent.parent.parent
app_dir = workspace_dir / "app"
sys.path.insert(0, str(app_dir))
sys.path.insert(0, str(workspace_dir))

from config import Config
from models.factory import ModelFactory
from memory.sumarizer import Summarizer
from memory.context_manager import estimate_tokens
from benchmarks.common.benchmark_runner import BenchmarkResultCollector
from benchmarks.memory.evaluate_memory_extraction import ResilientBenchmarkModel

try:
    import tiktoken
    _tokenizer = tiktoken.get_encoding("cl100k_base")
    def count_tokens(text: str) -> int:
        return len(_tokenizer.encode(text)) if text else 0
except Exception:
    def count_tokens(text: str) -> int:
        return estimate_tokens(text)


def run_summarization_benchmark():
    print("=" * 70)
    print("RUNNING PHASE 6 — SUMMARIZATION / CONTEXT COMPRESSION BENCHMARK")
    print("=" * 70)

    config = Config()
    raw_model = ModelFactory.create(config)
    model = ResilientBenchmarkModel(raw_model)
    summarizer = Summarizer(model=model)

    sample_turns = [
        ("user", "Hi, I am Rakesh. I work as a backend developer."),
        ("assistant", "Hello Rakesh! Nice to meet you. How can I help you today with backend development?"),
        ("user", "I am building a RAG pipeline with vector databases."),
        ("assistant", "That sounds exciting! Are you using ChromaDB or Pinecone for your vector store?"),
        ("user", "I chose ChromaDB for local persistence and zero config."),
        ("assistant", "ChromaDB is a great choice for lightweight local storage."),
        ("user", "Also, I prefer Python and FastAPI over Node.js."),
        ("assistant", "FastAPI is excellent for fast async Python web APIs."),
        ("user", "My goal is to optimize latency to under 200ms per request."),
        ("assistant", "To achieve sub-200ms latency, consider caching embeddings and running background tasks asynchronously."),
        ("user", "We implemented ThreadPoolExecutor for background memory extraction."),
        ("assistant", "ThreadPoolExecutor offloads heavy extraction off the main HTTP thread."),
        ("user", "We also use Reciprocal Rank Fusion for hybrid keyword and vector retrieval."),
        ("assistant", "RRF balances keyword matching with semantic vector distance effectively."),
        ("user", "I live in Seattle and enjoy running in my free time."),
        ("assistant", "Seattle has beautiful running trails like Green Lake and Burke-Gilman!"),
        ("user", "I am planning a trip to Japan next fall."),
        ("assistant", "Japan in autumn is stunning, especially Tokyo and Kyoto for fall foliage."),
        ("user", "We deploy our FastAPI application on Render using Docker multi-stage builds."),
        ("assistant", "Multi-stage builds keep Docker container images small and fast to deploy on Render."),
        ("user", "I am studying for the AWS Certified Solutions Architect exam."),
        ("assistant", "Best of luck! Focus on VPC, IAM, S3, and DynamoDB for the Solutions Architect exam."),
        ("user", "Can you help me design a rate limiter using token bucket algorithm?"),
        ("assistant", "Certainly! Token bucket rate limiting allows bursts while maintaining average throughput."),
        ("user", "We set a 10-message short-term memory threshold in our ChatAgent."),
        ("assistant", "That keeps active prompt context compact while retaining long-term summary context."),
        ("user", "Summarization happens whenever messages exceed 10 turns."),
        ("assistant", "Rolling summarization prevents context window overflow on long multi-turn sessions."),
        ("user", "We measure P50, P95, and P99 latencies for every endpoint."),
        ("assistant", "Percentile measurements provide accurate insights into tail latency under real traffic.")
    ]

    conversation_lengths = [12, 20, 30]
    collector = BenchmarkResultCollector()

    for length in conversation_lengths:
        subset = [{"role": r, "content": c} for r, c in sample_turns[:length]]
        pre_summary_text = "\n".join([f"{m['role']}: {m['content']}" for m in subset])
        
        pre_chars = len(pre_summary_text)
        pre_tokens = count_tokens(pre_summary_text)

        print(f"\nEvaluating conversation length = {length} messages:")
        print(f"  Pre-summary characters: {pre_chars} | Pre-summary tokens: {pre_tokens}")

        old_summary = ""
        summary_res = summarizer.summarize(old_summary, subset)
        post_chars = len(summary_res)
        post_tokens = count_tokens(summary_res)

        compression_ratio = round(post_tokens / pre_tokens, 4) if pre_tokens > 0 else 1.0
        token_reduction_pct = round(100.0 * (1.0 - (post_tokens / pre_tokens)), 2) if pre_tokens > 0 else 0.0

        print(f"  Post-summary characters: {post_chars} | Post-summary tokens: {post_tokens}")
        print(f"  Compression Ratio: {compression_ratio} (post/pre)")
        print(f"  Token Reduction: {token_reduction_pct}%")

        collector.add_result(f"pre_summary_tokens_{length}_msgs", pre_tokens, "tokens", "summarization", length)
        collector.add_result(f"post_summary_tokens_{length}_msgs", post_tokens, "tokens", "summarization", length)
        collector.add_result(f"compression_ratio_{length}_msgs", compression_ratio, "ratio", "summarization", length)
        collector.add_result(f"token_reduction_pct_{length}_msgs", token_reduction_pct, "percent", "summarization", length)

    collector.add_result("summarization_threshold_messages", 10, "messages", "summarization", 1, notes="Hardcoded agent short-term memory limit threshold = 10 messages")

    return collector.get_results()


if __name__ == "__main__":
    run_summarization_benchmark()
