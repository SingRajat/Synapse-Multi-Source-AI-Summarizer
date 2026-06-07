import csv
import os
import uuid
from datetime import datetime

BENCHMARK_FILE = "benchmarks/baseline_v3.csv"
CSV_HEADERS = [
    "timestamp", "source_type", "input_duration_mins", "chunk_count",
    "input_tokens", "output_tokens", "total_tokens", "map_input_tokens",
    "map_output_tokens", "reduce_input_tokens", "reduce_output_tokens",
    "context_window", "context_utilization", "request_attempts", "rate_limit_hits",
    "retry_overhead_secs", "ingest_latency", "chunk_latency", "map_latency",
    "reduce_latency", "end_to_end_latency", "bottleneck_stage", "bottleneck_percentage", "success", "error_type"
]

def init_benchmark_csv():
    """Ensures the benchmark directory and CSV file exist with headers."""
    os.makedirs(os.path.dirname(BENCHMARK_FILE), exist_ok=True)
    if not os.path.isfile(BENCHMARK_FILE):
        with open(BENCHMARK_FILE, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADERS)

