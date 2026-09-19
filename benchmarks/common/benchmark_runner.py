import time
import math
import statistics
from typing import List, Dict, Any


def calculate_quantiles(data: List[float]) -> Dict[str, float]:
    if not data:
        return {"p50": 0.0, "p95": 0.0, "p99": 0.0, "mean": 0.0, "min": 0.0, "max": 0.0, "std_dev": 0.0}
    sorted_data = sorted(data)
    n = len(sorted_data)
    
    def quantile(q: float) -> float:
        if n == 1:
            return sorted_data[0]
        pos = q * (n - 1)
        base = int(pos)
        rest = pos - base
        if base + 1 < n:
            return sorted_data[base] + rest * (sorted_data[base + 1] - sorted_data[base])
        else:
            return sorted_data[base]

    mean_val = statistics.mean(sorted_data)
    std_dev = statistics.stdev(sorted_data) if n > 1 else 0.0

    return {
        "p50": round(quantile(0.50), 2),
        "p95": round(quantile(0.95), 2),
        "p99": round(quantile(0.99), 2),
        "mean": round(mean_val, 2),
        "min": round(sorted_data[0], 2),
        "max": round(sorted_data[-1], 2),
        "std_dev": round(std_dev, 2)
    }


class BenchmarkResultCollector:
    def __init__(self):
        self.results: List[Dict[str, Any]] = []

    def add_result(
        self,
        metric: str,
        value: Any,
        unit: str,
        benchmark_name: str,
        sample_size: int,
        environment: str = "Local Python 3.12 / Windows",
        notes: str = ""
    ):
        entry = {
            "metric": metric,
            "value": value,
            "unit": unit,
            "benchmark_name": benchmark_name,
            "sample_size": sample_size,
            "environment": environment,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "notes": notes
        }
        self.results.append(entry)
        return entry

    def get_results(self) -> List[Dict[str, Any]]:
        return self.results
