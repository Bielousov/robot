import sys
import time
from pathlib import Path

import ollama
from dotenv import load_dotenv

# Path Logic
project_path = Path(__file__).parent.parent.parent.resolve()
if str(project_path) not in sys.path:
    sys.path.insert(0, str(project_path))

from models.llm.config.ollama import get_conversation_model_options, get_model_config
from models.llm.identity import build_identity_system_prompt

# ---------------------------------------------------------------------------
# Path / environment
# ---------------------------------------------------------------------------

load_dotenv(project_path / ".env")


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
config = get_model_config()
MODEL_NAME = config["model_name"]
OLLAMA_HOST = config["host"]

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

    # -----------------------------------------------------------------------
    # Warm-up
    # -----------------------------------------------------------------------

    print("[Ollama] Warming up engine...")

    try:
        # Consume the stream so the request fully completes.
        for _ in client.chat(
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
            stream=True,
            think=False,
            keep_alive=-1,
        ):
            pass

    except Exception as exc:
        print(f"[Ollama] Warm-up failed: {exc}")
        return

    # -----------------------------------------------------------------------
    # Timed inference
    # -----------------------------------------------------------------------

    print(f"[Ollama] Prompting Pip: '{PROMPT}'")
    print("\n--- Response ---")
    print("Pip: ", end="", flush=True)

    start_time = time.perf_counter()
    first_token_time = None
    answer_parts = []
    final_response = None

    try:
        stream = client.chat(
            model=MODEL_NAME,
            messages=messages,
            options=OPTIONS,
            stream=True,
            think=False,
            keep_alive=-1,
        )

        for chunk in stream:
            # ollama.ChatResponse supports model_dump()/dict-like access,
            # but getattr keeps this compatible with different client versions.
            message = getattr(chunk, "message", None)
            content = getattr(message, "content", "") if message else ""

            if content:
                if first_token_time is None:
                    first_token_time = time.perf_counter()

                answer_parts.append(content)
                print(content, end="", flush=True)

            # The final chunk contains the timing/token statistics.
            if getattr(chunk, "done", False):
                final_response = chunk

        end_time = time.perf_counter()

    except Exception as exc:
        print(f"\n[Ollama] Test failed: {exc}")
        return

    print("\n----------------------")

    # -----------------------------------------------------------------------
    # Results
    # -----------------------------------------------------------------------

    execution_time = end_time - start_time
    ttft = (
        first_token_time - start_time
        if first_token_time is not None
        else 0
    )

    answer = "".join(answer_parts)

    # Ollama fields are nanoseconds.
    eval_count = int(getattr(final_response, "eval_count", 0) or 0)
    eval_duration = (
        getattr(final_response, "eval_duration", 0) or 0
    ) / 1e9

    total_duration = (
        getattr(final_response, "total_duration", 0) or 0
    ) / 1e9

    load_duration = (
        getattr(final_response, "load_duration", 0) or 0
    ) / 1e9

    tokens_per_second = (
        eval_count / eval_duration
        if eval_duration > 0
        else 0
    )

    generation_time = (
        execution_time - ttft
        if first_token_time is not None
        else execution_time
    )

    print(f"TTFT:               {ttft:.3f} seconds")
    print(f"Generation Time:    {generation_time:.3f} seconds")
    print(f"Inference Latency:  {execution_time:.3f} seconds")
    print(f"Load Duration:      {load_duration:.3f} seconds")
    print(f"Output Tokens:      {eval_count}")
    print(f"Tokens/sec:         {tokens_per_second:.2f}")
    print(f"Total Duration:     {total_duration:.3f} seconds")

    if execution_time < 3:
        print("🚀 Note: Exceptional speed.")
    elif execution_time < 7:
        print("⚡ Note: Standard performance.")
    else:
        print("🐢 Note: High latency detected.")


if __name__ == "__main__":
    run_test()