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
