import os
import sys
from pathlib import Path

workspace_dir = Path(__file__).resolve().parent.parent.parent
app_dir = workspace_dir / "app"
sys.path.insert(0, str(app_dir))
sys.path.insert(0, str(workspace_dir))

from config import Config
from benchmarks.common.benchmark_runner import BenchmarkResultCollector


def run_cost_analysis_benchmark(avg_input_tokens: float = 350.0, avg_output_tokens: float = 120.0):
    print("=" * 70)
    print("RUNNING PHASE 14 — FINANCIAL COST ANALYSIS BENCHMARK")
    print("=" * 70)

    config = Config()
    provider = getattr(config, "provider", "groq").lower().strip()
    model_name = getattr(config, "model_name", "groq/compound-mini").strip()

    # Empirical pricing rates (Pricing as of September 2026 / Official Public Pricing)
    # Groq / Compound-Mini / Llama 3 8B: $0.05 / 1M input tokens, $0.08 / 1M output tokens
    # OpenAI GPT-4o-mini: $0.150 / 1M input tokens, $0.600 / 1M output tokens
    # OpenAI text-embedding-3-small: $0.020 / 1M tokens

    if provider == "openai":
        input_cost_per_1m = 0.150
        output_cost_per_1m = 0.600
        embed_cost_per_1m = 0.020
    elif provider == "groq":
        input_cost_per_1m = 0.050
        output_cost_per_1m = 0.080
        embed_cost_per_1m = 0.000  # Running local fallback or standard free tier
    elif provider in ["bedrock", "amazon_bedrock", "aws_bedrock"]:
        input_cost_per_1m = 0.300
        output_cost_per_1m = 1.200
        embed_cost_per_1m = 0.010
    else:
        input_cost_per_1m = 0.100
        output_cost_per_1m = 0.400
        embed_cost_per_1m = 0.000

    cost_per_req_input = (avg_input_tokens / 1_000_000.0) * input_cost_per_1m
    cost_per_req_output = (avg_output_tokens / 1_000_000.0) * output_cost_per_1m
    total_cost_per_req = cost_per_req_input + cost_per_req_output

    cost_100_reqs = total_cost_per_req * 100.0
    cost_1000_reqs = total_cost_per_req * 1000.0

    collector = BenchmarkResultCollector()
    collector.add_result("configured_llm_provider", provider, "name", "cost_analysis", 1)
    collector.add_result("configured_llm_model", model_name, "name", "cost_analysis", 1)
    collector.add_result("avg_input_tokens_per_req", avg_input_tokens, "tokens", "cost_analysis", 1)
    collector.add_result("avg_output_tokens_per_req", avg_output_tokens, "tokens", "cost_analysis", 1)
    collector.add_result("avg_total_tokens_per_req", avg_input_tokens + avg_output_tokens, "tokens", "cost_analysis", 1)
    collector.add_result("estimated_cost_per_req_usd", round(total_cost_per_req, 6), "USD", "cost_analysis", 1)
    collector.add_result("estimated_cost_per_100_reqs_usd", round(cost_100_reqs, 4), "USD", "cost_analysis", 100)
    collector.add_result("estimated_cost_per_1000_reqs_usd", round(cost_1000_reqs, 4), "USD", "cost_analysis", 1000)

    print(f"Configured Provider : {provider} ({model_name})")
    print(f"Avg Input Tokens    : {avg_input_tokens} tokens/req")
    print(f"Avg Output Tokens   : {avg_output_tokens} tokens/req")
    print(f"Cost per Request    : ${total_cost_per_req:.6f} USD")
    print(f"Cost per 100 Reqs   : ${cost_100_reqs:.4f} USD")
    print(f"Cost per 1,000 Reqs : ${cost_1000_reqs:.4f} USD")

    return collector.get_results()


if __name__ == "__main__":
    run_cost_analysis_benchmark()
