import os
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

def get_model_config() -> Dict[str, Any]:
    """Load Ollama model settings from environment variables."""

    return {
        "model_hef": os.getenv("HAILO_MODEL_HEF", "Qwen2.5-1.5B-Instruct.hef"),
        "identity": os.getenv("OLLAMA_SYSTEM_PROMPT", ""),
    }

def get_conversation_model_options() -> Dict[str, Any]:
    return {
        "max_generated_tokens": int(os.getenv("HAILO_NUM_PREDICT", 64)),
        "do_sample": bool(int(os.getenv("HAILO_DO_SAMPLE", 0))),
        "temperature": float(os.getenv("HAILO_TEMPERATURE", 0.8)),
        "top_k": int(os.getenv("HAILO_TOP_K", 40)),
        "top_p": float(os.getenv("HAILO_TOP_P", 0.9)),
    }
    
def get_classifier_model_options() -> Dict[str, Any]:
    return {
        "max_generated_tokens": 4,
        "seed": 42,
        "temperature": 0.0,
        "top_k": 1,
        "top_p": 1.0,
    }