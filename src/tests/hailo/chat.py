import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from hailo_platform import VDevice
from hailo_platform.genai import LLM


# -------- paths / config --------

PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")

MODEL_HEF = os.getenv("HAILO_MODEL_HEF", "Qwen2.5-1.5B-Instruct.hef")
MODELS_DIR = PROJECT_ROOT / "src" / "lib" / "hailo" / "models"
HEF = MODELS_DIR / f"{MODEL_HEF}"

SYSTEM_PROMPT = (
    "You are Pip, a robot. "
    "Your name is Pip. "
    "Speak as Pip, not as an assistant. "
    "Answer directly and naturally. "
    "Use English. "
    "Keep replies concise, normally 1-2 sentences."
)

def generate(llm, text):
    prompt = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text", 
                    "text": text,
                }
            ],
        },
    ]

    start = time.perf_counter()
    first_token_time = None
    token_count = 0
    response = ""

    with llm.generate(
        prompt=prompt,
        temperature=0.8,
        max_generated_tokens=50,
    ) as generation:
        for chunk in generation:
            if chunk == "<|im_end|>":
                continue

            if first_token_time is None:
                first_token_time = time.perf_counter()

            token_count += 1
            response += chunk
            print(chunk, end="", flush=True)

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
    if not HEF.is_file():
        print(f"[Hailo] ERROR: HEF not found: {HEF}")
        sys.exit(2)

    print(f"[Hailo] Model: {MODEL_HEF}")
    print(f"[Hailo] HEF:   {HEF}")
    print("[Hailo] Loading model...")

    vdevice = VDevice()
    llm = LLM(vdevice, str(HEF))

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

            # Start each CLI prompt with a clean context.
            llm.clear_context()

    except KeyboardInterrupt:
        print("\n\n[Hailo] Ctrl+C received. Exiting...")

    finally:
        print("[Hailo] Releasing model...")
        llm.clear_context()
        llm.release()
        vdevice.release()


if __name__ == "__main__":
    main()