import os
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

def get_model_config() -> Dict[str, Any]:
    """Load Ollama model settings from environment variables.

    Only ever the trained/personality model (src/models/ollama/train.sh,
    registered under OLLAMA_MODEL_NAME) - there is no base-model fallback.
    Its Modelfile already carries the right generation defaults and a baked-in
    SYSTEM prompt, so nothing here overrides them.
    """

    return {
        "host": os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        "model_name": os.getenv("OLLAMA_MODEL_NAME", "pip"),
    }