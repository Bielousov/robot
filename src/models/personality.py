import os
import sys
import time
from typing import Any, Dict, Optional


def build_personality_system_prompt() -> str:
    """Build the baked-in personality prompt for the custom Ollama model."""
    name = os.getenv("NAME", "Pip")
    role = os.getenv("ROBOT_ROLE", "Robot")
    user_name = os.getenv("USER_NAME", "human")
    hardware = os.getenv("HARDWARE", "Raspberry Pi 5")
    location = os.getenv("CONTEXT_LOCATION", "Planet Earth")
    language = os.getenv("LANGUAGE", "English")
    base_prompt = os.getenv("OLLAMA_SYSTEM_PROMPT", "You are Robot.")

    return (
        f"IDENTITY [MANDATORY]: You are {name}.\n"
        f"- Name: {name}\n"
        f"- Role: {role}\n"
        f"- Human operator: {user_name}\n"
        f"- Hardware: {hardware}\n"
        f"- Location: {location}\n\n"
        "SYSTEM INSTRUCTIONS:\n"
        f"{base_prompt}\n\n"
        "SENSORS:\n"
        f"- Language: {language}\n\n"
        "CONTEXT RULES:\n"
        f"- {user_name} is the human speaking to you, not your identity.\n"
        f"- When the user says 'I am {user_name}', interpret that as the user's identity.\n"
        f"- You MUST respond as {name}, not as an assistant.\n"
        "- Never claim to have 'no name' or 'no identity'."
    )


def get_llm_model_config() -> Dict[str, Any]:
    """Load Ollama model settings from environment variables."""
    options = {
        "num_ctx": int(os.getenv("OLLAMA_CONTEXT_LENGTH", 1024)),
        "num_thread": int(os.getenv("OLLAMA_THREADS", 4)),
        "temperature": float(os.getenv("OLLAMA_TEMPERATURE", 1.0)),
        "num_predict": int(os.getenv("OLLAMA_NUM_PREDICT", 40)),
        "repeat_penalty": float(os.getenv("OLLAMA_REPEAT_PENALTY", 1.2)),
        "top_k": int(os.getenv("OLLAMA_TOP_K", 40)),
        "top_p": float(os.getenv("OLLAMA_TOP_P", 0.9)),
        "stop": ["User:", "Pip:"],
    }

    return {
        "base_model": os.getenv("OLLAMA_BASE_MODEL", "gemma3:270m"),
        "model_name": os.getenv("OLLAMA_MODEL_NAME", "pip"),
        "system_prompt": build_personality_system_prompt(),
        "options": options,
    }


def create_personality_model(
    client: Any,
    model_name: str,
    base_model: str,
    system_prompt: str,
    options: Dict[str, Any],
    max_attempts: int = 8,
    retry_delay_seconds: int = 2,
) -> bool:
    """Create a custom Ollama model from a base model and bake in the system prompt.

    The personality is embedded at model creation time. Later requests should use the
    model name only and must not send a per-request `system` override.
    """
    print(f"[Robot] Initializing personality for '{model_name}' based on {base_model} model")

    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            stream = client.create(
                model=model_name,
                from_=base_model,
                system=system_prompt,
                parameters=options,
                stream=True,
            )

            for chunk in stream:
                status = chunk.get("status", "")
                completed = chunk.get("completed")
                total = chunk.get("total")

                if total and completed and total > 0:
                    total_mb = total / (1024 * 1024)
                    loaded_pct = (completed / total) * 100
                    sys.stdout.write(
                        f"\rLoading model {base_model} ({total_mb:.1f} MB): {loaded_pct:.1f} %"
                    )
                    sys.stdout.flush()
                elif status and status != "success":
                    sys.stdout.write(f"\r{status}...{' ' * 20}")
                    sys.stdout.flush()

                if status == "success" or chunk.get("done"):
                    print(f"\n[-] Loading personality in to the memory…")
                    client.generate(
                        model=model_name,
                        prompt='',
                        stream=False,
                        keep_alive=-1,
                    )
                    return True
        except Exception as exc:  # pragma: no cover - runtime dependent branch
            last_error = exc
            message = str(exc)
            if "not found" in message.lower() or "404" in message:
                if attempt < max_attempts:
                    print(
                        f"\n[Robot] Model not ready yet (attempt {attempt}/{max_attempts}). "
                        "Waiting for SD card flush..."
                    )
                    time.sleep(retry_delay_seconds)
                    continue
            print(f"\n[Error] Could not build personality model: {exc}")
            return False

    if last_error is not None:
        print(f"\n[Error] Could not build personality model after retries: {last_error}")

    return False
