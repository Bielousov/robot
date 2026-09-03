import os
import signal
import time
from pathlib import Path

import ollama
import psutil

# Path configuration
LIB_PATH = Path(__file__).parent.parent.resolve()
OLLAMA_PATH = LIB_PATH / "ollama" / "dist"
MODELS_PATH = LIB_PATH / "ollama" / "models"
OLLAMA_BIN = OLLAMA_PATH / "bin" / "ollama"
LOGS_PATH = OLLAMA_PATH / "server.log"

OLLAMA_URL = "http://localhost:11434"

class OllamaClient:
    """Wraps the Ollama server/client so Mind can talk to it generically.

    Exposes the same surface a future Hailo-backed client would need
    (load_model, chat, stop) so Mind can switch backends without changing
    its own logic.
    """

    def __init__(self, host: str = OLLAMA_URL):
        self.process = None
        self._client = ollama.Client(host=host)
        self._prepare_environment()
        self.start_server()

    def _prepare_environment(self):
        """RPi5 Stability Flags."""
        os.makedirs(MODELS_PATH, exist_ok=True)
        env_vars = {
            "OLLAMA_MODELS": str(MODELS_PATH),
            "OLLAMA_MAX_LOADED_MODELS": "1",
            "OLLAMA_NUM_PARALLEL": "1",
            "OLLAMA_LLM_LIBRARY": "cpu",
        }
        os.environ.update(env_vars)

    def start_server(self):
        """Checks that the external Ollama service is already running."""
        try:
            self._client.ps()
            print("[Ollama] Ollama service is running.")
        except Exception as exc:
            raise RuntimeError(
                "Ollama service is not running. Start it via 'sudo systemctl start ollama.service'."
            ) from exc

    def load_model(self, model_name: str):
        """Pull the given model into Ollama."""
        print(f"[Ollama] Pulling model '{model_name}' into Ollama...")
        self._client.pull(model_name)
        print(f"[Ollama] Model '{model_name}' is ready.")
    

    def chat(self, **kwargs):
        """Passthrough to the underlying ollama.Client.chat()."""
        return self._client.chat(**kwargs)

    def stop(self):
        if self.process:
            print("[-] Stopping server...")
            os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
            self.process = None

    def _force_stop_server(self):
        """Wipes old processes to free up RAM."""
        for proc in psutil.process_iter(['name']):
            if 'ollama' in (proc.info['name'] or "").lower():
                try:
                    os.kill(proc.pid, signal.SIGKILL)
                except Exception:
                    pass
        time.sleep(1)
