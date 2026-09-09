import os
import signal
import subprocess
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

# How long to wait for a freshly spawned server to accept connections.
SERVER_START_TIMEOUT_S = 30
SERVER_POLL_INTERVAL_S = 0.5

class OllamaClient:
    """Wraps the Ollama server/client so Mind can talk to it generically.

    Exposes the same surface a future Hailo-backed client would need
    (load_model, chat, stop) so Mind can switch backends without changing
    its own logic. Manages its own 'ollama serve' subprocess via the CLI
    binary rather than assuming an external service (e.g. systemd) is
    already running.
    """

    def __init__(
        self,
        host: str = OLLAMA_URL,
        lora_path: str = "",
        personalized_model: str = "",
    ):
        self.model = None
        self.process = None
        self.lora_path = Path(lora_path).expanduser() if lora_path else None
        self.personalized_model = personalized_model.strip()
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
        """Starts 'ollama serve' via the CLI binary if it isn't already up."""
        try:
            self._client.ps()
            print("[Ollama] Ollama service is already running.")
            return
        except Exception:
            pass

        if not OLLAMA_BIN.is_file():
            raise RuntimeError(
                f"Ollama binary not found at {OLLAMA_BIN}. Run lib/ollama/install.sh first."
            )

        print(f"[Ollama] Starting '{OLLAMA_BIN} serve'...")
        with open(LOGS_PATH, "ab") as log_file:
            self.process = subprocess.Popen(
                [str(OLLAMA_BIN), "serve"],
                stdout=log_file,
                stderr=subprocess.STDOUT,
                env=os.environ.copy(),
                start_new_session=True,
            )

        deadline = time.monotonic() + SERVER_START_TIMEOUT_S
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                raise RuntimeError(
                    f"'ollama serve' exited early (code {self.process.returncode}). "
                    f"Check logs at {LOGS_PATH}."
                )
            try:
                self._client.ps()
                print("[Ollama] Ollama service is running.")
                return
            except Exception:
                time.sleep(SERVER_POLL_INTERVAL_S)

        self.stop()
        raise RuntimeError(
            f"Timed out waiting for 'ollama serve' to become ready after {SERVER_START_TIMEOUT_S}s."
        )

    def load_model(self, model: str):
        """Pull the base model and bind an optional LoRA-derived model."""
        print(f"[Ollama] Pulling model '{model}' into Ollama...")
        self._client.pull(model)

        if self.lora_path:
            if not self.lora_path.is_file():
                raise FileNotFoundError(
                    f"Ollama LoRA adapter not found at: {self.lora_path}"
                )

            if not self.personalized_model:
                raise ValueError(
                    "PERSONALIZED_MODEL must be set when LLM_LORA_PATH is configured."
                )

            print(
                f"[Ollama] Creating '{self.personalized_model}' from '{model}' "
                f"with adapter '{self.lora_path}'..."
            )
            self._client.create(
                model=self.personalized_model,
                from_=model,
                adapters=[str(self.lora_path.resolve())],
            )
            self.model = self.personalized_model
        else:
            self.model = model

        print(f"[Ollama] Model '{self.model}' is ready.")

    def chat(self, **kwargs):
        """Passthrough to the underlying ollama.Client.chat(), bound to this
        client's model and using this client's fixed request defaults."""
        kwargs["model"] = self.model
        kwargs.setdefault("stream", True)
        kwargs.setdefault("think", False)
        kwargs.setdefault("keep_alive", -1)
        return self._client.chat(**kwargs)

    def stop(self):
        """Stops the server this client spawned, if any. Leaves an
        externally managed service (e.g. systemd) running untouched."""
        if not self.process:
            return

        print("[Ollama] Stopping server...")
        try:
            os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            self.process.wait(timeout=10)
        except Exception:
            try:
                os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
            except Exception:
                pass
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
