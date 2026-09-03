import sys
import time
from pathlib import Path

import ollama
from dotenv import load_dotenv

from models.llm.config import get_conversation_model_options, get_model_config
from models.llm.identity import build_identity_system_prompt


# ---------------------------------------------------------------------------
# Path / environment
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

OLLAMA_HOST = "http://localhost:11434"

config = get_model_config()
MODEL_NAME = config["model_name"]

SYSTEM_PROMPT = build_identity_system_prompt()
OPTIONS = get_conversation_model_options()

PROMPT_TEXT = " ".join(sys.argv[1:]) or "Tell me about yourself"

def run_test():
    print("[Test] Initializing Ollama client...")
    print(f"[Test] Model: {MODEL_NAME}")
    print(f"[Test] Ollama: {OLLAMA_HOST}")

    client = ollama.Client(host=OLLAMA_HOST)

    # -----------------------------------------------------------------------
    # Verify Ollama
    # -----------------------------------------------------------------------

    try:
        client.ps()
        print("[Test] Ollama service is running.")
    except Exception as exc:
        print(f"[Test] ERROR: Ollama service is unavailable: {exc}")
        return

    # -----------------------------------------------------------------------
    # Make sure model exists / is loaded
    # -----------------------------------------------------------------------

    try:
        print(f"[Test] Ensuring model '{MODEL_NAME}' is available...")
        client.pull(MODEL_NAME)
        print(f"[Test] Model '{MODEL_NAME}' is ready.")
    except Exception as exc:
        print(f"[Test] ERROR: Could not prepare model: {exc}")
        return

    # -----------------------------------------------------------------------
    # Warm-up
    # -----------------------------------------------------------------------

    print("[Test] Warming up engine...")

    try:
        client.chat(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": "System check.",
                },
            ],
            options=OPTIONS,
            stream=False,
            think=False,
            keep_alive=-1,
        )
    except Exception as exc:
        print(f"[Test] Warm-up failed: {exc}")
        return

    # -----------------------------------------------------------------------
    # Timed inference
    # -----------------------------------------------------------------------

    print(f"[Test] Prompting Pip: '{PROMPT}'")

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": PROMPT,
        },
    ]

    start_time = time.perf_counter()

    try:
        response = client.chat(
            model=MODEL_NAME,
            messages=messages,
            options=OPTIONS,
            stream=False,
            think=False,
            keep_alive=-1,
        )

        end_time = time.perf_counter()

    except Exception as exc:
        print(f"[Test] Test failed: {exc}")
        return

    # -----------------------------------------------------------------------
    # Results
    # -----------------------------------------------------------------------

    execution_time = end_time - start_time

    answer = response.get("message", {}).get("content", "")

    eval_count = int(response.get("eval_count", 0))
    eval_duration = response.get("eval_duration", 0) / 1e9
    total_duration = response.get("total_duration", 0) / 1e9
    load_duration = response.get("load_duration", 0) / 1e9

    tokens_per_second = (
        eval_count / eval_duration
        if eval_duration > 0
        else 0
    )

    print("\n--- Response ---")
    print(f"Pip: {answer}")
    print("----------------------")

    print(f"⏱️  Inference Latency: {execution_time:.2f} seconds")
    print(f"📊 Total Duration:     {total_duration:.2f} seconds")
    print(f"📦 Load Duration:      {load_duration:.2f} seconds")
    print(f"🔢 Output Tokens:      {eval_count}")
    print(f"🚀 Tokens/sec:         {tokens_per_second:.2f}")

    if execution_time < 3:
        print("🚀 Note: Exceptional speed.")
    elif execution_time < 7:
        print("⚡ Note: Standard performance.")
    else:
        print("🐢 Note: High latency detected.")


if __name__ == "__main__":
    run_test()