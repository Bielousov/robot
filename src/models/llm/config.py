import os
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

def get_model_config() -> Dict[str, Any]:
    """Load Ollama model settings from environment variables."""

    return {
        "base_model": os.getenv("OLLAMA_BASE_MODEL", "qwen2.5:0.5b"),
        "model_name": os.getenv("OLLAMA_BASE_MODEL", "qwen2.5:0.5b"),
        "options": {
            "num_ctx": int(os.getenv("OLLAMA_CONTEXT_LENGTH", 1024)),
            "num_predict": int(os.getenv("OLLAMA_NUM_PREDICT", 40)),
            "num_thread": int(os.getenv("OLLAMA_THREADS", 4)),
            "temperature": float(os.getenv("OLLAMA_TEMPERATURE", 0.9)),
            "repeat_penalty": float(os.getenv("OLLAMA_REPEAT_PENALTY", 1.2)),
            "top_k": int(os.getenv("OLLAMA_TOP_K", 40)),
            "top_p": float(os.getenv("OLLAMA_TOP_P", 0.9)),
            "stop": ["User:"],
        }
    }

def get_conversation_model_options() -> Dict[str, Any]:
    config = get_model_config()
    return config["options"]

def get_classifier_model_options() -> Dict[str, Any]:
    return {
        "num_ctx": 1024,
        "num_predict": 4,
        "num_thread": int(os.getenv("OLLAMA_THREADS", 4)),
        "repeat_penalty": 1.0,
        "temperature": 0.0,
        "top_k": 1,
        "top_p": 1.0,
    }