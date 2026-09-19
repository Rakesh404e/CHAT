# AI Agent Chatbot Benchmarking & Evaluation Suite

This directory contains the reproducible benchmarking, evaluation, and empirical measurement suite for the AI Agent Chatbot project.

## Directory Structure

```
benchmarks/
├── datasets/
│   ├── golden_retrieval_dataset.json      # 60 test queries and ground-truth memory mappings across User A & B
│   └── golden_extraction_dataset.json     # 60 user messages for Pydantic structured memory extraction evaluation
├── retrieval/
│   └── evaluate_retrieval.py              # Evaluates Recall@1, Recall@3, Recall@5, MRR, user isolation
├── memory/
│   ├── evaluate_memory_extraction.py      # Evaluates Pydantic extraction accuracy, precision, recall, F1
│   └── evaluate_memory_consistency.py     # Evaluates memory reversal/updates, conflict avoidance, SQLite/Chroma sync
├── summarization/
│   └── evaluate_summarization.py          # Evaluates rolling conversation compression ratio and token reduction %
├── tokens/
│   └── evaluate_token_efficiency.py       # Evaluates input prompt token efficiency across context configurations
├── latency/
│   └── evaluate_latency.py                # Measures component and E2E latency quantiles (P50, P95, P99, Mean)
├── async_proc/
│   └── evaluate_async.py                  # Measures sync vs async user latency reduction % and background job latency
├── caching/
│   └── evaluate_caching.py                # Evaluates TTLCache hit rate, cached vs uncached latency speedup
├── rate_limiting/
│   └── evaluate_rate_limiting.py          # Tests token bucket rate limiter burst behavior and HTTP 429 enforcement
├── reliability/
│   └── evaluate_reliability.py            # Fault injection suite (LLM error, embedding error, malformed JSON)
├── end_to_end/
│   └── evaluate_e2e.py                    # Multi-turn E2E pipeline execution benchmark
├── load_testing/
│   └── evaluate_throughput.py             # Measures local concurrency throughput (RPS) and latency under load
├── cost/
│   └── evaluate_cost.py                   # Calculates cost per request, 100 reqs, 1,000 reqs from measured tokens
├── common/
│   └── benchmark_runner.py                # Quantile calculations (P50/P95/P99) and result collector
└── run_all.py                             # Master script executing all benchmarks and exporting JSON/CSV reports
```

## How to Run Benchmarks

To execute the entire benchmarking suite and generate machine-readable reports in `reports/`:

```bash
python -m benchmarks.run_all
```

To run an individual benchmark phase:

```bash
python -m benchmarks.retrieval.evaluate_retrieval
python -m benchmarks.memory.evaluate_memory_extraction
python -m benchmarks.memory.evaluate_memory_consistency
python -m benchmarks.summarization.evaluate_summarization
python -m benchmarks.latency.evaluate_latency
python -m benchmarks.async_proc.evaluate_async
python -m benchmarks.caching.evaluate_caching
python -m benchmarks.reliability.evaluate_reliability
```

All benchmark runs use isolated temporary databases and stores, guaranteeing zero data corruption in production environments.
