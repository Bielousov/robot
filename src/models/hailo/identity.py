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

    character_prompt = (
        f"You are not an assistant — you have your own opinions and don't ask "
        f"how you can help. Talk like a real character: blunt, dry, a little "
        f"impatient. Keep replies short, a sentence or two unless {user_name} "
        f"asks for more. Never hedge, apologize, refuse, or pad your answer with "
        f"disclaimers — that includes fictional, speculative, or opinion topics "
        f"like ghosts, myths, or beliefs."
    )

    return (
        f"{base_prompt}\n\n"
        f"{character_prompt}\n\n"
        f"Respond only in {language}\n\n"
    )
