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

from models.hailo.config import get_conversation_model_options
from models.hailo.identity import build_identity_system_prompt

# -------- path / config --------

PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")

MODEL_HEF = os.getenv("MODEL_HEF", "Qwen2.5-1.5B-Instruct")
MODELS_DIR = PROJECT_ROOT / "src" / "lib" / "hailo" / "models"
NODEL_PATH = MODELS_DIR / f"{MODEL_HEF}"

ITERATIONS = 10
WARMUP_RUNS = 1

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
    print("[Benchmark] Initializing Hailo...")

    if not HEF.is_file():
        print(f"[Benchmark] ERROR: HEF not found: {NODEL_PATH}")
        sys.exit(2)

    print(f"[Benchmark] Model: {MODEL_HEF}")
    print(f"[Benchmark] HEF:   {NODEL_PATH}")

    # Model creation/loading is NOT timed.
    vdevice = VDevice()
    llm = LLM(vdevice, str(NODEL_PATH))

    try:
        print(f"[Benchmark] Warming up model ({WARMUP_RUNS} runs)...")

        for _ in range(WARMUP_RUNS):
            run_once(llm)
            llm.clear_context()

        print(f"[Benchmark] Running {ITERATIONS} timed iterations...")

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