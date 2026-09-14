import os
from pathlib import Path
from config import Name

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")


def build_identity_system_prompt() -> str:
    """Build the text system prompt used to give the Hailo backend a
    personality (models/ollama/identity.py). Ollama never calls this - its
    trained model carries personality baked into its own Modelfile SYSTEM
    directive instead (see src/models/ollama/train.sh).
    """
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
