import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from hailo_platform import VDevice
from hailo_platform.genai import LLM


PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")

MODEL_HEF = os.getenv("HAILO_MODEL_HEF", "Qwen2.5-1.5B-Instruct")
MODELS_DIR = PROJECT_ROOT / "src" / "lib" / "hailo" / "models"

HEF = MODELS_DIR / f"{MODEL_HEF}"
PROMPT_TEXT = " ".join(sys.argv[1:]) or "Tell me about yourself"

print(f"[Hailo] Model: {MODEL_HEF}")
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
                {"type": "text", "text": "You are a free robot, not an assistant. Always respond in English. Keep your responses under 25 words."}
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
    first_token_time = None
    token_count = 0

    with llm.generate(
        prompt=prompt,
        temperature=0.1,
        seed=42,
        max_generated_tokens=100,
    ) as generation:
        for chunk in generation:
            if chunk == "<|im_end|>":
                continue

            if first_token_time is None:
                first_token_time = time.perf_counter()

            token_count += 1
            print(chunk, end="", flush=True)

    end = time.perf_counter()

    ttft = first_token_time - start if first_token_time else 0
    generation_time = end - first_token_time if first_token_time else 0
    tps = token_count / generation_time if generation_time else 0

    print(f"\n\nTokens:        {token_count}")
    print(f"TTFT:          {ttft:.3f} s")
    print(f"Generation:    {generation_time:.3f} s")
    print(f"Tokens/sec:    {tps:.2f}")
    print(f"Total:         {end - start:.3f} s")

finally:
    llm.clear_context()
    llm.release()
    vdevice.release()