import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from hailo_platform import VDevice
from hailo_platform.genai import LLM

project_path = Path(__file__).parent.parent.parent.resolve()
if str(project_path) not in sys.path:
    sys.path.insert(0, str(project_path))

from models.hailo.config import get_model_config, get_conversation_model_options
from models.hailo.identity import build_identity_system_prompt

# -------- paths / config --------

PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")

config = get_model_config()

MODELS_DIR = PROJECT_ROOT / "src" / "lib" / "hailo" / "models"
MODEL_PATH = MODELS_DIR / f"{config['model_hef']}"

SYSTEM_PROMPT = build_identity_system_prompt()
OPTIONS = get_conversation_model_options()

def generate(llm, text):
    prompt = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": text},
    ]

    start = time.perf_counter()
    first_token_time = None
    token_count = 0
    response = ""

    with llm.generate(
        prompt=prompt,
        **OPTIONS,
    ) as generation:
        for chunk in generation:
            if chunk == "<|im_end|>":
                continue

            if first_token_time is None:
                first_token_time = time.perf_counter()

            token_count += 1
            response += chunk
            print(chunk, end="", flush=True)

    llm.clear_context()

    end = time.perf_counter()

    total_time = end - start

    if first_token_time is not None:
        ttft = first_token_time - start
        generation_time = end - first_token_time
        tps = token_count / generation_time if generation_time > 0 else 0
    else:
        ttft = 0
        generation_time = 0
        tps = 0

    return {
        "response": response,
        "tokens": token_count,
        "ttft": ttft,
        "generation_time": generation_time,
        "total_time": total_time,
        "tps": tps,
    }


def main():
    if not MODEL_PATH.is_file():
        print(f"[Hailo] ERROR: HEF not found: {MODEL_PATH}")
        sys.exit(2)

    print(f"[Hailo] Model: {config['model_hef']}")
    print(f"[Hailo] HEF:   {MODEL_PATH}")
    print("[Hailo] Loading model...")

    vdevice = VDevice()
    llm = LLM(vdevice, str(MODEL_PATH))

    print("[Hailo] Model loaded.")
    print("Type a prompt and press Enter. Ctrl+C to quit.\n")

    try:
        while True:
            try:
                text = input("You: ").strip()
            except EOFError:
                break

            if not text:
                continue

            print("Pip: ", end="", flush=True)

            stats = generate(llm, text)

            print()
            print(
                f"[Stats] "
                f"Tokens: {stats['tokens']} | "
                f"TTFT: {stats['ttft']:.3f}s | "
                f"Gen: {stats['generation_time']:.3f}s | "
                f"TPS: {stats['tps']:.2f} | "
                f"Total: {stats['total_time']:.3f}s"
            )
            print()

            # Keep the model context for multi-turn conversation.

    except KeyboardInterrupt:
        print("\n\n[Hailo] Ctrl+C received. Exiting...")

    finally:
        llm.clear_context()
        # llm.release()
        # vdevice.release()


if __name__ == "__main__":
    main()