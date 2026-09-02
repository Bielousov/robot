import sys
import time

from hailo_platform import VDevice
from hailo_platform.genai import LLM

HEF = sys.argv[1] if len(sys.argv) > 1 else "qwen2.5-1.5b-instruct.hef"
PROMPT = " ".join(sys.argv[2:]) or "What is the capital of Canada?"

vdevice = VDevice()
llm = LLM(vdevice, HEF)

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