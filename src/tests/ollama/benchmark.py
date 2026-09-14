import statistics
import sys
import time
from pathlib import Path

import ollama
from dotenv import load_dotenv

project_path = Path(__file__).parent.parent.parent.resolve()
if str(project_path) not in sys.path:
    sys.path.insert(0, str(project_path))

from models.ollama.config.ollama import get_model_config

ITERATIONS = 10
WARMUP_RUNS = 1

# ---------------------------------------------------------------------------
# Path / environment
# ---------------------------------------------------------------------------

load_dotenv(project_path / ".env")

# ---------------------------------------------------------------------------
# Configuration
#
# Only ever the trained/personality model (OLLAMA_MODEL_NAME) - no base-model
# fallback, no generation options, no separate system prompt. Its Modelfile
# already carries the right defaults and a baked-in SYSTEM prompt; sending an
# explicit system message here (even an empty one) would override it instead
# of adding to it.
# ---------------------------------------------------------------------------
config = get_model_config()
OLLAMA_HOST = config["host"]
MODEL_NAME = config["model_name"]

PROMPT = (
    "Briefly explain why the sky appears blue to a human observer, "
    "using exactly one sentence without using the word 'scattering'."
)

MESSAGES = [{"role": "user", "content": PROMPT}]


def run_once(client):
    """Execute one direct Ollama request and return its elapsed time."""
    start = time.perf_counter()

    for _ in client.chat(
        model=MODEL_NAME,
        messages=MESSAGES,
        stream=True,
        think=False,
        keep_alive=-1,
    ):
        pass

    return time.perf_counter() - start


def benchmark():
    print("[Ollama] Initializing Ollama client...")
    print(f"[Ollama] Model: {MODEL_NAME}")
    print(f"[Ollama] Ollama: {OLLAMA_HOST}")

    client = ollama.Client(host=OLLAMA_HOST)

    try:
        client.ps()
        print("[Ollama] Ollama service is running.")
    except Exception as exc:
        print(f"[Ollama] ERROR: Ollama service is unavailable: {exc}")
        return

    try:
        print(f"[Ollama] Ensuring model '{MODEL_NAME}' is available...")
        # A trained/local model is created via `ollama create` and never
        # published to any registry - pulling it would fail with a 404, so
        # just verify it's already registered instead.
        client.show(MODEL_NAME)
        print(f"[Ollama] Model '{MODEL_NAME}' is ready.")
    except Exception as exc:
        print(f"[Ollama] ERROR: Could not prepare model: {exc}")
        return

    print(f"[Ollama] Warming up model ({WARMUP_RUNS} runs)...")
    for _ in range(WARMUP_RUNS):
        run_once(client)

    print(f"[Ollama] Running {ITERATIONS} timed iterations...")
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