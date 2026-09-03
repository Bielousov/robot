import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from hailo_platform import VDevice
from hailo_platform.genai import LLM

# Path Logic
project_path = Path(__file__).parent.parent.parent.resolve()
if str(project_path) not in sys.path:
    sys.path.insert(0, str(project_path))

from models.hailo.config import get_conversation_model_options
from models.hailo.identity import build_identity_system_prompt

PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")

MODEL_HEF = os.getenv("HAILO_MODEL_HEF", "Qwen2.5-1.5B-Instruct")
MODELS_DIR = PROJECT_ROOT / "src" / "lib" / "hailo" / "models"
HEF = MODELS_DIR / f"{MODEL_HEF}"

OPTIONS = get_conversation_model_options()
PROMPT = " ".join(sys.argv[1:]) or "Tell me about yourself"
SYSTEM_PROMPT = build_identity_system_prompt()

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
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": PROMPT,
        }
    ]

    # ------------------------------------------------------------------
    # Timed inference
    # ------------------------------------------------------------------

    print("\nResponse:")

    start = time.perf_counter()
    first_token_time = None
    token_count = 0

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
    # llm.release()
    # vdevice.release()