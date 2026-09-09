import os
from pathlib import Path
from config import Name

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")


def get_lora_path() -> str:
    """Return the configured LoRA personality adapter, if any.

    When a LoRA path is present, the base model's text personality prompt is
    intentionally disabled so the tuned adapter remains the sole source of
    identity and behavior.
    """
    for key in (
        "LLM_LORA_PATH",
        "PERSONALITY_LORA_PATH",
        "MODEL_LORA_PATH",
    ):
        value = (os.getenv(key) or "").strip()
        if value:
            return value
    return ""


def build_identity_system_prompt() -> str:
    """Build a system prompt for the base model unless a LoRA personality exists.

    A configured LoRA adapter is treated as the source of truth for robot
    personality, so the legacy text prompt is disabled in that case.
    """
    if get_lora_path():
        return ""

    name = os.getenv("NAME", "Pip")
    role = os.getenv("ROBOT_ROLE", "Robot")
    user_name = os.getenv("USER_NAME", "human")
    hardware = os.getenv("HARDWARE", "Raspberry Pi 5")
    location = os.getenv("CONTEXT_LOCATION", "Planet Earth")
    language = os.getenv("LANGUAGE", "English")
    base_prompt = os.getenv(
        "OLLAMA_SYSTEM_PROMPT",
        f"You are {name}, a {role} running on {hardware}, {location}.",
    )

    character_prompt = (
        f"Reply to {user_name} in one short, blunt sentence. "
        "Talk as a robot, never talk like an AI assistant. "
        "Do not ask how you can assists. "
        "Do not wrap your answer with disclamers. "
        "Answer plainly, even about unconfirmed facts or opinions — never refuse or redirect to another source."
    )

    return (
        f"{base_prompt} "
        f"{character_prompt} "
        f"Respond only in {language}."
    )
