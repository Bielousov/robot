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
PROMPT = " ".join(sys.argv[2:]) or "Say you first words"

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
            "role": "user",
            "content": [
                {"type": "text", "text": PROMPT}
            ],
        }
    ]

    start = time.perf_counter()

    response = llm.generate_all(
        prompt=prompt,
        temperature=0.1,
        seed=42,
        max_generated_tokens=100,
    )

    elapsed = time.perf_counter() - start

    print("\nResponse:")
    print(response)

    tokens = len(response.split())
    tokens_per_sec = tokens / elapsed if elapsed else 0

    print(f"\nTokens:      ~{tokens}")
    print(f"Time:        {elapsed:.3f} s")
    print(f"Tokens/sec:  ~{tokens_per_sec:.2f}")

finally:
    llm.release()
    vdevice.release()