import os
import time
import statistics
from ollama import Client

# -------- config --------
MODEL = "pip"
ITERATIONS = 10
WARMUP_RUNS = 3
PROMPT = "Explain what 2 + 2 equals in one short sentence."
MAX_TOKENS = 32

OPTIONS = {}

# -------- setup --------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../../"))
MODELS_DIR = os.path.join(PROJECT_ROOT, "lib/ollama/models")
os.environ["OLLAMA_MODELS"] = MODELS_DIR

client = Client(host="http://localhost:11434")


def run_once():
    start = time.perf_counter()
    client.chat(
        model=MODEL,
        messages=[{"role": "user", "content": PROMPT}],
        options=OPTIONS,
        keep_alive=-1,
    )
    return time.perf_counter() - start


def benchmark():
    print("[Benchmark] Warming up model...")
    for _ in range(WARMUP_RUNS):
        run_once()

    print("[Benchmark] Running timed iterations...")
    times = []
    for i in range(ITERATIONS):
        t = run_once()
        times.append(t)
        print(f"  Run {i+1}: {t:.2f}s")

    print("\n====== RESULTS ======")
    print(f"Runs:        {ITERATIONS}")
    print(f"Min:         {min(times):.2f}s")
    print(f"Avg:         {statistics.mean(times):.2f}s")
    print(f"Median:      {statistics.median(times):.2f}s")
    print(f"P95:         {statistics.quantiles(times, n=20)[18]:.2f}s")
    print(f"Max:         {max(times):.2f}s")


if __name__ == "__main__":
    benchmark()
