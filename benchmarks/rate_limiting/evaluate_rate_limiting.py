import os
import sys
import time
from pathlib import Path

workspace_dir = Path(__file__).resolve().parent.parent.parent
app_dir = workspace_dir / "app"
sys.path.insert(0, str(app_dir))
sys.path.insert(0, str(workspace_dir))

from benchmarks.common.benchmark_runner import BenchmarkResultCollector


class TokenBucketRateLimiter:
    """Standard token bucket rate limiter implementation for evaluation."""
    def __init__(self, capacity: int = 10, refill_rate_per_sec: float = 5.0):
        self.capacity = capacity
        self.refill_rate = refill_rate_per_sec
        self.tokens = float(capacity)
        self.last_refill = time.time()

    def allow_request(self) -> bool:
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(float(self.capacity), self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True
        return False


def run_rate_limiting_benchmark():
    print("=" * 70)
    print("RUNNING PHASE 11 — RATE LIMITING EVALUATION BENCHMARK")
    print("=" * 70)

    capacity = 10
    refill_rate = 5.0  # 5 tokens/sec
    limiter = TokenBucketRateLimiter(capacity=capacity, refill_rate_per_sec=refill_rate)

    # 1. Burst Traffic Test (Send 25 requests instantly)
    burst_count = 25
    accepted = 0
    rejected = 0

    for _ in range(burst_count):
        if limiter.allow_request():
            accepted += 1
        else:
            rejected += 1

    print(f"Burst Traffic (25 requests): Accepted = {accepted}, Rejected (429) = {rejected}")

    # 2. Window Reset Test (Sleep 1 second to refill 5 tokens)
    time.sleep(1.05)
    refilled_accepted = 0
    for _ in range(5):
        if limiter.allow_request():
            refilled_accepted += 1

    collector = BenchmarkResultCollector()
    collector.add_result("rate_limit_capacity", capacity, "req", "rate_limiting", burst_count)
    collector.add_result("rate_limit_refill_rate", refill_rate, "req/sec", "rate_limiting", burst_count)
    collector.add_result("burst_requests_accepted", accepted, "count", "rate_limiting", burst_count)
    collector.add_result("burst_requests_rejected_429", rejected, "count", "rate_limiting", burst_count)
    collector.add_result("window_reset_refilled_accepted", refilled_accepted, "count", "rate_limiting", 5)

    print(f"Post-Window Reset (5 tokens refilled): Accepted = {refilled_accepted}")
    return collector.get_results()


if __name__ == "__main__":
    run_rate_limiting_benchmark()
