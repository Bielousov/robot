import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from hailo_platform import VDevice
from hailo_platform.genai import LLM


PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")

MODEL_NAME = os.getenv("HAILO_MODEL", "Qwen2.5-1.5B-Instruct")
MODELS_DIR = PROJECT_ROOT / "src" / "lib" / "hailo" / "models"

HEF = Path(sys.argv[1]) if len(sys.argv) > 1 else MODELS_DIR / f"{MODEL_NAME}.hef"
PROMPT_TEXT = " ".join(sys.argv[2:]) or "Say hello in your character"

print(f"[Hailo] Model: {MODEL_NAME}")
print(f"[Hailo] HEF:   {HEF}")

if not HEF.is_file():
    print(f"[Hailo] ERROR: HEF not found: {HEF}")
    sys.exit(2)

vdevice = VDevice()
llm = LLM(vdevice, str(HEF))

try:
    prompt = [
        {
            "role": "system",
            "content": [
                {"type": "text", "text": "Always respond in English."}
            ],
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": PROMPT_TEXT}
            ],
        }
    ]

    print("\nResponse:")

    start = time.perf_counter()
    response = ""

    with llm.generate(
        prompt=prompt,
        temperature=0.1,
        seed=42,
        max_generated_tokens=100,
    ) as generation:
        for chunk in generation:
            if chunk != "<|im_end|>":
                print(chunk, end="", flush=True)
                response += chunk

    elapsed = time.perf_counter() - start

    print(f"\n\nTime: {elapsed:.3f} s")

finally:
    llm.clear_context()
    llm.release()
    vdevice.release()