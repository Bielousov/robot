import sys
import time
from pathlib import Path

import ollama
from dotenv import load_dotenv

# Path Logic
project_path = Path(__file__).parent.parent.parent.resolve()
if str(project_path) not in sys.path:
    sys.path.insert(0, str(project_path))

from models.llm.config import get_conversation_model_options, get_model_config
from models.llm.identity import build_identity_system_prompt


# ---------------------------------------------------------------------------
# Path / environment
# ---------------------------------------------------------------------------

load_dotenv(project_path / ".env")


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

OLLAMA_HOST = "http://localhost:11434"

config = get_model_config()
MODEL_NAME = config["model_name"]

OPTIONS = get_conversation_model_options()
PROMPT = " ".join(sys.argv[1:]) or "Tell me about yourself"
SYSTEM_PROMPT = build_identity_system_prompt()

def run_test():
    print("[Ollama] Initializing Ollama client...")
    print(f"[Ollama] Model: {MODEL_NAME}")
    print(f"[Ollama] Ollama: {OLLAMA_HOST}")

    client = ollama.Client(host=OLLAMA_HOST)

    # -----------------------------------------------------------------------
    # Verify Ollama
    # -----------------------------------------------------------------------

    try:
        client.ps()
        print("[Ollama] Ollama service is running.")
    except Exception as exc:
        print(f"[Ollama] ERROR: Ollama service is unavailable: {exc}")
        return

    # -----------------------------------------------------------------------
    # Make sure model exists / is loaded
    # -----------------------------------------------------------------------

    try:
        print(f"[Ollama] Ensuring model '{MODEL_NAME}' is available...")
        client.pull(MODEL_NAME)
        print(f"[Ollama] Model '{MODEL_NAME}' is ready.")
    except Exception as exc:
        print(f"[Ollama] ERROR: Could not prepare model: {exc}")
        return

    # -----------------------------------------------------------------------
    # Warm-up
    # -----------------------------------------------------------------------

    print("[Ollama] Warming up engine...")

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
                    "content": PROMPT,
                },
            ],
            options=OPTIONS,
            stream=False,
            think=False,
            keep_alive=-1,
        )
    except Exception as exc:
        print(f"[Ollama] Warm-up failed: {exc}")
        return

    # -----------------------------------------------------------------------
    # Timed inference
    # -----------------------------------------------------------------------

    print(f"[Ollama] Prompting Pip: '{PROMPT}'")

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
        print(f"[Ollama] Test failed: {exc}")
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

    print(f"Inference Latency: {execution_time:.2f} seconds")
    print(f"Load Duration:      {load_duration:.2f} seconds")
    print(f"Output Tokens:      {eval_count}")
    print(f"Tokens/sec:         {tokens_per_second:.2f}")
    print(f"Total Duration:     {total_duration:.2f} seconds")

    if execution_time < 3:
        print("🚀 Note: Exceptional speed.")
    elif execution_time < 7:
        print("⚡ Note: Standard performance.")
    else:
        print("🐢 Note: High latency detected.")


if __name__ == "__main__":
    run_test()