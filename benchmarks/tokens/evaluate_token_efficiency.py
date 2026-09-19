import os
import sys
from pathlib import Path

workspace_dir = Path(__file__).resolve().parent.parent.parent
app_dir = workspace_dir / "app"
sys.path.insert(0, str(app_dir))
sys.path.insert(0, str(workspace_dir))

from memory.context_manager import ContextManager, estimate_tokens
from benchmarks.common.benchmark_runner import BenchmarkResultCollector

try:
    import tiktoken
    _tokenizer = tiktoken.get_encoding("cl100k_base")
    def count_tokens(text: str) -> int:
        return len(_tokenizer.encode(text)) if text else 0
except Exception:
    def count_tokens(text: str) -> int:
        return estimate_tokens(text)


def run_token_efficiency_benchmark():
    print("=" * 70)
    print("RUNNING PHASE 7 — CONTEXT / TOKEN EFFICIENCY BENCHMARK")
    print("=" * 70)

    cm = ContextManager()

    recent_messages = [
        {"role": "user", "content": "I am working on an AI agent backend."},
        {"role": "assistant", "content": "That is awesome! What features are you building?"},
        {"role": "user", "content": "Hybrid vector retrieval with ChromaDB and SQLite."},
        {"role": "assistant", "content": "Hybrid retrieval balances exact key matches with semantic vector similarity."},
        {"role": "user", "content": "We also implemented rolling conversation summarization."},
        {"role": "assistant", "content": "Rolling summarization prevents context window saturation on long sessions."}
    ]

    summary = "User is Rakesh, a backend engineer building an AI agent chatbot using FastAPI, SQLite, ChromaDB, and Groq inference."
    memories = [
        {"content": "PREFERENCE [programming_language]: User prefers Python and FastAPI", "metadata": {"memory_type": "preference"}},
        {"content": "GOAL [target_role]: Crack Senior AI Backend Engineer interview", "metadata": {"memory_type": "goal"}},
        {"content": "FACT [location]: User resides in Seattle Washington", "metadata": {"memory_type": "fact"}},
        {"content": "PLAN [migration]: Plan to migrate storage to PostgreSQL in Q4", "metadata": {"memory_type": "plan"}},
        {"content": "DECISION [concurrency]: Decided to use ThreadPoolExecutor for background tasks", "metadata": {"memory_type": "decision"}}
    ]

    current_message = "What tech stack choices did I make for my AI agent backend?"

    # Configuration A: Recent conversation only
    ctx_a = cm.build_context(summary=None, recent_messages=recent_messages, current_message=current_message, long_term_memories=None)
    str_a = "\n".join([f"{m['role']}: {m['content']}" for m in ctx_a])
    tokens_a = count_tokens(str_a)

    # Configuration B: Recent conversation + summary
    ctx_b = cm.build_context(summary=summary, recent_messages=recent_messages, current_message=current_message, long_term_memories=None)
    str_b = "\n".join([f"{m['role']}: {m['content']}" for m in ctx_b])
    tokens_b = count_tokens(str_b)

    # Configuration C: Recent conversation + summary + long term memory
    ctx_c = cm.build_context(summary=summary, recent_messages=recent_messages, current_message=current_message, long_term_memories=memories)
    str_c = "\n".join([f"{m['role']}: {m['content']}" for m in ctx_c])
    tokens_c = count_tokens(str_c)

    collector = BenchmarkResultCollector()
    collector.add_result("input_tokens_config_a_recent_only", tokens_a, "tokens", "token_efficiency", 1, notes="Recent history only")
    collector.add_result("input_tokens_config_b_recent_plus_summary", tokens_b, "tokens", "token_efficiency", 1, notes="Recent history + conversation summary")
    collector.add_result("input_tokens_config_c_full_context", tokens_c, "tokens", "token_efficiency", 1, notes="Recent history + summary + categorized long term memory")

    print("\n--- TOKEN EFFICIENCY COMPARISON ---")
    print(f"Config A (Recent Only): {tokens_a} input tokens")
    print(f"Config B (Recent + Summary): {tokens_b} input tokens (+{tokens_b - tokens_a} tokens)")
    print(f"Config C (Recent + Summary + Long-Term Memory): {tokens_c} input tokens (+{tokens_c - tokens_b} tokens from memory)")

    return collector.get_results()


if __name__ == "__main__":
    run_token_efficiency_benchmark()
