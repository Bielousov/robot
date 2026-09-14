import os
import statistics
import sys
import time
from pathlib import Path

import ollama
from dotenv import load_dotenv

project_path = Path(__file__).parent.parent.parent.resolve()
if str(project_path) not in sys.path:
    sys.path.insert(0, str(project_path))

from models.ollama.config.ollama import get_conversation_model_options, get_model_config
from models.ollama.identity import build_identity_system_prompt

ITERATIONS = 10
WARMUP_RUNS = 1

# ---------------------------------------------------------------------------
# Path / environment
# ---------------------------------------------------------------------------

load_dotenv(project_path / ".env")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
config = get_model_config()
OLLAMA_HOST = config["host"]

# Prefer the personality-trained model (src/models/ollama/train.sh, installed
# under OLLAMA_MODEL_NAME) over the plain base model tag once one exists.
TRAINED_MODEL_NAME = os.getenv("OLLAMA_MODEL_NAME", "").strip()
USING_TRAINED_MODEL = bool(TRAINED_MODEL_NAME)
MODEL_NAME = TRAINED_MODEL_NAME or config["model_name"]

OPTIONS = get_conversation_model_options()
PROMPT = (
    "Briefly explain why the sky appears blue to a human observer, "
    "using exactly one sentence without using the word 'scattering'."
)

# A trained model already has its personality baked in via the Modelfile's
# SYSTEM directive - skip Mind's separate text system prompt so we don't
# layer a redundant/conflicting one on top (same reasoning as Mind.py).
SYSTEM_PROMPT = "" if USING_TRAINED_MODEL else build_identity_system_prompt()

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
        if USING_TRAINED_MODEL:
            # Trained/local models are created via `ollama create` and never
            # published to any registry - pulling one fails with a 404, so
            # just verify it's already registered instead.
            client.show(MODEL_NAME)
        else:
            client.pull(MODEL_NAME)
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