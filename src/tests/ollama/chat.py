import sys
import time
from pathlib import Path

import ollama
from dotenv import load_dotenv

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
SYSTEM_PROMPT = build_identity_system_prompt()


def generate(client, messages):
    """Stream one Ollama response and return its text and timing metrics."""
    start = time.perf_counter()
    first_token_time = None
    token_count = 0
    response_parts = []
    final_response = None

    stream = client.chat(
        model=MODEL_NAME,
        messages=messages,
        options=OPTIONS,
        stream=True,
        think=False,
        keep_alive=-1,
    )

    for chunk in stream:
        message = getattr(chunk, "message", None)
        content = getattr(message, "content", "") if message else ""

        if content:
            if first_token_time is None:
                first_token_time = time.perf_counter()

            response_parts.append(content)
            print(content, end="", flush=True)

        if getattr(chunk, "done", False):
            final_response = chunk

    end = time.perf_counter()
    total_time = end - start
    ttft = (
        first_token_time - start
        if first_token_time is not None
        else 0
    )
    generation_time = (
        end - first_token_time
        if first_token_time is not None
        else total_time
    )

    eval_count = int(getattr(final_response, "eval_count", 0) or 0)
    eval_duration = (
        getattr(final_response, "eval_duration", 0) or 0
    ) / 1e9
    tokens_per_second = (
        eval_count / eval_duration
        if eval_duration > 0
        else 0
    )

    return {
        "response": "".join(response_parts),
        "tokens": eval_count or token_count,
        "ttft": ttft,
        "generation_time": generation_time,
        "total_time": total_time,
        "tokens_per_second": tokens_per_second,
    }


def main():
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
        client.pull(MODEL_NAME)
        print(f"[Ollama] Model '{MODEL_NAME}' is ready.")
    except Exception as exc:
        print(f"[Ollama] ERROR: Could not prepare model: {exc}")
        return

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    print("Type a prompt and press Enter. Ctrl+C to quit.\n")

    try:
        while True:
            try:
                text = input("You: ").strip()
            except EOFError:
                break

            if not text:
                continue

            messages.append({"role": "user", "content": text})
            print("Pip: ", end="", flush=True)

            try:
                stats = generate(client, messages)
            except Exception as exc:
                messages.pop()
                print(f"\n[Ollama] Chat failed: {exc}")
                continue

            messages.append({"role": "assistant", "content": stats["response"]})

            print()
            print(
                f"[Stats] Tokens: {stats['tokens']} | "
                f"TTFT: {stats['ttft']:.3f}s | "
                f"Gen: {stats['generation_time']:.3f}s | "
                f"TPS: {stats['tokens_per_second']:.2f} | "
                f"Total: {stats['total_time']:.3f}s"
            )
            print()

    except KeyboardInterrupt:
        print("\n\n[Ollama] Ctrl+C received. Exiting...")


if __name__ == "__main__":
    main()
