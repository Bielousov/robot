import os
from pathlib import Path
from config import Name

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")


def build_identity_system_prompt() -> str:
    """Build a per-request identity prompt for the base Ollama model."""
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

    character_prompt = f"Reply to {user_name} in one short, blunt sentence. Never talk like an AI assistant. Do not wrap your answer with disclamers. Do not ask how you can assists."

    return (
        f"{base_prompt} "
        f"{character_prompt} "
        f"Respond only in {language}."
    )


def build_example_exchange() -> list:
    """One-shot example demonstrating the target voice, to prime style via example
    rather than instruction alone — small models follow a shown tone far more
    reliably than a described one."""
    return [
        {"role": "user", "content": "Can you help me with something?"},
        {"role": "assistant", "content": "Depends what it is. Spit it out."},
    ]
