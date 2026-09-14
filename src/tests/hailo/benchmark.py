import os
import sys
import time
import statistics
from pathlib import Path

from dotenv import load_dotenv
from hailo_platform import VDevice
from hailo_platform.genai import LLM

project_path = Path(__file__).parent.parent.parent.resolve()
if str(project_path) not in sys.path:
    sys.path.insert(0, str(project_path))

# -------- path / config --------

PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")

MODEL_HEF = "Qwen2.5-1.5B-Instruct.hef"
MODELS_DIR = PROJECT_ROOT / "src" / "lib" / "hailo" / "models"
MODEL_PATH = MODELS_DIR / MODEL_HEF

ITERATIONS = 10
WARMUP_RUNS = 1

OPTIONS = {
    "max_generated_tokens": 64,
    "do_sample": True,
    "temperature": 0.7,
    "top_k": 40,
    "top_p": 0.9,
}
PROMPT = (
    "Briefly explain why the sky appears blue to a human observer, "
    "using exactly one sentence without using the word 'scattering'."
)
MESSAGES = [
    {"role": "user", "content": PROMPT},
]

def run_once(llm):
    """Executes a single inference and returns the duration."""

    start = time.perf_counter()

    response = ""

    with llm.generate(
        prompt=MESSAGES,
        **OPTIONS,
    ) as generation:
        for chunk in generation:
            if chunk != "<|im_end|>":
                response += chunk

    elapsed = time.perf_counter() - start

    return elapsed, response


def benchmark():
    print("[Hailo] Initializing Hailo...")

    if not MODEL_PATH.is_file():
        print(f"[Hailo] ERROR: HEF not found: {MODEL_PATH}")
        sys.exit(2)

    print(f"[Hailo] Model: {MODEL_HEF}")
    print(f"[Hailo] HEF:   {MODEL_PATH}")
    print("[Hailo] Loading model...")

    # Model creation/loading is NOT timed.
    vdevice = VDevice()
    llm = LLM(vdevice, str(MODEL_PATH))

    try:
        print(f"[Hailo] Warming up model ({WARMUP_RUNS} runs)...")

        for _ in range(WARMUP_RUNS):
            run_once(llm)
            llm.clear_context()

        print(f"[Hailo] Running {ITERATIONS} timed iterations...")

        times = []

        for i in range(ITERATIONS):
            # Keep prompt/context identical for every iteration.
            llm.clear_context()

            t, response = run_once(llm)
            times.append(t)

            print(f"  Run {i + 1:02d}: {t:.2f}s")

        print("\n" + "=" * 21)
        print("   BENCHMARK RESULTS   ")
        print("=" * 21)

        print(f"Model:            {MODEL_HEF}")
        print(f"Total Iterations: {ITERATIONS}")
        print(f"Fastest Run:      {min(times):.2f}s")
        print(f"Average Time:     {statistics.mean(times):.2f}s")
        print(f"Median Time:      {statistics.median(times):.2f}s")

        if ITERATIONS >= 4:
            p95 = statistics.quantiles(times, n=20)[18]
            print(f"P95 Latency:      {p95:.2f}s")

        print(f"Slowest Run:      {max(times):.2f}s")
        print("=" * 21)

    finally:
        llm.clear_context()
        #llm.release()
        #vdevice.release()


if __name__ == "__main__":
    benchmark()