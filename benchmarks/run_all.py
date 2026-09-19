import os
import sys
import json
import csv
import time
from pathlib import Path

workspace_dir = Path(__file__).resolve().parent.parent
app_dir = workspace_dir / "app"
sys.path.insert(0, str(app_dir))
sys.path.insert(0, str(workspace_dir))

from benchmarks.retrieval.evaluate_retrieval import run_retrieval_benchmark
from benchmarks.memory.evaluate_memory_extraction import run_memory_extraction_benchmark
from benchmarks.memory.evaluate_memory_consistency import run_memory_consistency_benchmark
from benchmarks.summarization.evaluate_summarization import run_summarization_benchmark
from benchmarks.tokens.evaluate_token_efficiency import run_token_efficiency_benchmark
from benchmarks.latency.evaluate_latency import run_latency_benchmark
from benchmarks.async_proc.evaluate_async import run_async_processing_benchmark
from benchmarks.caching.evaluate_caching import run_caching_benchmark
from benchmarks.rate_limiting.evaluate_rate_limiting import run_rate_limiting_benchmark
from benchmarks.reliability.evaluate_reliability import run_reliability_benchmark
from benchmarks.end_to_end.evaluate_e2e import run_e2e_benchmark
from benchmarks.load_testing.evaluate_throughput import run_throughput_benchmark
from benchmarks.cost.evaluate_cost import run_cost_analysis_benchmark


def export_results(all_results, reports_dir):
    json_path = reports_dir / "benchmark_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)

    csv_path = reports_dir / "benchmark_results.csv"
    if all_results:
        fieldnames = list(all_results[0].keys())
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_results)


def main():
    print("=" * 80)
    print("AI AGENT CHATBOT BENCHMARKING SUITE — MASTER EXECUTION")
    print("=" * 80)

    reports_dir = workspace_dir / "reports"
    reports_dir.mkdir(exist_ok=True)

    all_results = []

    phases = [
        ("Phase 3: Retrieval", run_retrieval_benchmark),
        ("Phase 4: Memory Extraction", run_memory_extraction_benchmark),
        ("Phase 5: Memory Consistency", run_memory_consistency_benchmark),
        ("Phase 6: Summarization", run_summarization_benchmark),
        ("Phase 7: Token Efficiency", run_token_efficiency_benchmark),
        ("Phase 8: Latency", lambda: run_latency_benchmark(num_runs=15)),
        ("Phase 9: Async Processing", lambda: run_async_processing_benchmark(num_runs=10)),
        ("Phase 10: Caching", lambda: run_caching_benchmark(num_runs=20)),
        ("Phase 11: Rate Limiting", run_rate_limiting_benchmark),
        ("Phase 12: Reliability", run_reliability_benchmark),
        ("Phase 13: End-to-End", lambda: run_e2e_benchmark(num_turns=6)),
        ("Phase 15: Throughput", lambda: run_throughput_benchmark(concurrency_levels=[1, 3, 5], requests_per_level=5)),
    ]

    for name, fn in phases:
        print(f"\n--- Executing {name} ---")
        try:
            res = fn()
            all_results.extend(res)
            export_results(all_results, reports_dir)
        except Exception as e:
            print(f"Error in {name}: {e}")

    # Extract measured tokens for cost benchmark
    in_tok = next((r["value"] for r in all_results if r["metric"] == "input_tokens_config_c_full_context"), 350.0)
    out_tok = 120.0

    print("\n--- Executing Phase 14: Cost Analysis ---")
    try:
        res = run_cost_analysis_benchmark(avg_input_tokens=in_tok, avg_output_tokens=out_tok)
        all_results.extend(res)
        export_results(all_results, reports_dir)
    except Exception as e:
        print(f"Error in Phase 14: Cost Analysis: {e}")

    print("\n" + "=" * 80)
    print(f"BENCHMARK COMPLETE! Total Metrics Recorded: {len(all_results)}")
    print(f"Results exported to: {reports_dir}")
    print("=" * 80)


if __name__ == "__main__":
    main()
