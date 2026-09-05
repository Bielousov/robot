from pathlib import Path

from hailo_platform.genai import LLM

from lib.hailo.device import get_vdevice

# Path configuration
LIB_PATH = Path(__file__).parent.parent.resolve()
MODELS_PATH = LIB_PATH / "hailo" / "models"

# HailoRT's genai LLM emits this sentinel token to mark the end of a turn;
# it is not part of the generated text.
END_OF_TURN_TOKEN = "<|im_end|>"


class HailoClient:
    """Wraps a Hailo VDevice + genai.LLM so Mind can talk to it generically.

    Exposes the same surface OllamaClient does (load_model, chat, stop) so
    Mind can switch backends without changing its own logic. `chat()` yields
    (or returns) Ollama-shaped chunks/responses -
    {"message": {"content": ...}, "done": ...} - so callers don't need to
    know which backend is in use.
    """

    def __init__(self):
        self.model = None
        self._vdevice = get_vdevice()
        self._llm = None

    def load_model(self, model: str):
        """Load the given HEF file onto this client's Hailo device."""
        self.model = model
        hef_path = self._resolve_hef_path(model)

        print(f"[Hailo] Loading model '{hef_path.name}'...")

        if not hef_path.is_file():
            raise FileNotFoundError(f"Hailo model not found at: {hef_path}")

        if self._llm is not None:
            self._llm.release()

        self._llm = LLM(self._vdevice, str(hef_path))

        print(f"[Hailo] Model '{hef_path.name}' is ready.")

    def _resolve_hef_path(self, model: str) -> Path:
        path = Path(model)
        return path if path.is_absolute() else MODELS_PATH / path

    def chat(self, **kwargs):
        """Run one generation, matching ollama.Client.chat()'s wire shape.

        Only `messages`, `options` and `stream` are used; other kwargs
        (model, think, keep_alive, logprobs, ...) are Ollama-specific and
        silently ignored here - this client is bound to a single model via
        load_model(), and HailoRT has no such concepts.
        """
        messages = kwargs.get("messages", [])
        options = kwargs.get("options", {}) or {}
        stream = kwargs.get("stream", True)

        generation = self._llm.generate(prompt=messages, **options)

        if stream:
            return self._stream(generation)

        content = self._generate_all(generation)
        return {"message": {"content": content}, "done": True}

    def _stream(self, generation):
        # HailoRT only allows a system-role message as the very first prompt
        # sent to a context; clear_context() after each turn resets that so
        # every call can safely include a fresh system message again.
        with generation as tokens:
            for chunk in tokens:
                if chunk == END_OF_TURN_TOKEN:
                    continue
                yield {"message": {"content": chunk}, "done": False}

        self._llm.clear_context()
        yield {"message": {"content": ""}, "done": True}

    def _generate_all(self, generation) -> str:
        content = ""
        with generation as tokens:
            for chunk in tokens:
                if chunk == END_OF_TURN_TOKEN:
                    continue
                content += chunk

        self._llm.clear_context()
        return content

    def stop(self):
        # Deliberately not releasing self._vdevice here: it's the shared
        # HailoRT device (lib/hailo/device.py) used by Ears' Whisper engine
        # too, so this client must not tear it down on its own.
        if self._llm is not None:
            self._llm.clear_context()
            self._llm.release()
            self._llm = None
