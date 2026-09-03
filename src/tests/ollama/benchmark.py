import statistics
import sys
import time
from pathlib import Path

import ollama
from dotenv import load_dotenv

project_path = Path(__file__).parent.parent.parent.resolve()
if str(project_path) not in sys.path:
    sys.path.insert(0, str(project_path))

from models.ollama.config import get_conversation_model_options, get_model_config
from models.ollama.identity import build_identity_system_prompt


OLLAMA_HOST = "http://localhost:11434"
ITERATIONS = 10
WARMUP_RUNS = 1

load_dotenv(project_path / ".env")
config = get_model_config()
MODEL_NAME = config["model_name"]
OPTIONS = get_conversation_model_options()
PROMPT = (
    "Briefly explain why the sky appears blue to a human observer, "
    "using exactly one sentence without using the word 'scattering'."
)
SYSTEM_PROMPT = build_identity_system_prompt()

MESSAGES = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user", "content": PROMPT},
]

def run_once(client):
    """Execute one direct Ollama request and return its elapsed time."""
    start = time.perf_counter()

    for _ in client.chat(
        model=MODEL_NAME,
        messages=MESSAGES,
        options=OPTIONS,
        stream=True,
        think=False,
        keep_alive=-1,
    ):
        pass

    return time.perf_counter() - start


def benchmark():
    print("[Benchmark] Initializing Ollama client...")
    print(f"[Benchmark] Model: {MODEL_NAME}")
    print(f"[Benchmark] Ollama: {OLLAMA_HOST}")

    client = ollama.Client(host=OLLAMA_HOST)

    try:
        client.ps()
        print("[Benchmark] Ollama service is running.")
    except Exception as exc:
        print(f"[Benchmark] ERROR: Ollama service is unavailable: {exc}")
        return

    try:
        print(f"[Benchmark] Ensuring model '{MODEL_NAME}' is available...")
        client.pull(MODEL_NAME)
        print(f"[Benchmark] Model '{MODEL_NAME}' is ready.")
    except Exception as exc:
        print(f"[Benchmark] ERROR: Could not prepare model: {exc}")
        return

    print(f"[Benchmark] Warming up model ({WARMUP_RUNS} runs)...")
    for _ in range(WARMUP_RUNS):
        run_once(client)

    print(f"[Benchmark] Running {ITERATIONS} timed iterations...")
    times = []
    for index in range(ITERATIONS):
        elapsed = run_once(client)
        times.append(elapsed)
        print(f"  Run {index + 1:02d}: {elapsed:.2f}s")

    print("\n" + "=" * 21)
    print("   BENCHMARK RESULTS   ")
    print("=" * 21)
    print(f"Total Iterations: {ITERATIONS}")
    print(f"Fastest Run:      {min(times):.2f}s")
    print(f"Average Time:     {statistics.mean(times):.2f}s")
    print(f"Median Time:      {statistics.median(times):.2f}s")

    if ITERATIONS >= 4:
        p95 = statistics.quantiles(times, n=20)[18]
        print(f"P95 Latency:      {p95:.2f}s")

    print(f"Slowest Run:      {max(times):.2f}s")
    print("=" * 21)


if __name__ == "__main__":
    benchmark()