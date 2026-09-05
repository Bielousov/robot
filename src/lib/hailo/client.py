import time
from pathlib import Path
from typing import Optional

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

        return self._generate_all(generation)

    @staticmethod
    def _metrics(start_time: float, first_token_time: Optional[float], end_time: float, token_count: int) -> dict:
        """Ollama-shaped timing/throughput fields, in nanoseconds like Ollama's own.

        HailoRT's genai LLM reports none of this itself (no token counts or
        phase timings), so it's approximated from wall-clock measurements
        taken around the generation loop: prompt_eval covers the time before
        the first token arrives, eval covers everything after. load_duration
        is always 0 here since the model stays resident between calls - there
        is no per-call load cost to measure. eval_count is the number of
        chunks HailoRT yielded, which approximates but isn't guaranteed to
        equal the model's actual token count.
        """
        prompt_eval_duration = (first_token_time - start_time) if first_token_time else (end_time - start_time)
        eval_duration = (end_time - first_token_time) if first_token_time else 0
        return {
            "total_duration": int((end_time - start_time) * 1e9),
            "load_duration": 0,
            "prompt_eval_duration": int(prompt_eval_duration * 1e9),
            "eval_duration": int(eval_duration * 1e9),
            "eval_count": token_count,
        }

    def _stream(self, generation):
        start_time = time.perf_counter()
        first_token_time = None
        token_count = 0

        # HailoRT only allows a system-role message as the very first prompt
        # sent to a context; clear_context() after each turn resets that so
        # every call can safely include a fresh system message again.
        with generation as tokens:
            for chunk in tokens:
                if chunk == END_OF_TURN_TOKEN:
                    continue
                if first_token_time is None:
                    first_token_time = time.perf_counter()
                token_count += 1
                yield {"message": {"content": chunk}, "done": False}

        end_time = time.perf_counter()
        self._llm.clear_context()

        yield {
            "message": {"content": ""},
            "done": True,
            **self._metrics(start_time, first_token_time, end_time, token_count),
        }

    def _generate_all(self, generation) -> dict:
        start_time = time.perf_counter()
        first_token_time = None
        token_count = 0
        content = ""

        with generation as tokens:
            for chunk in tokens:
                if chunk == END_OF_TURN_TOKEN:
                    continue
                if first_token_time is None:
                    first_token_time = time.perf_counter()
                token_count += 1
                content += chunk

        end_time = time.perf_counter()
        self._llm.clear_context()

        return {
            "message": {"content": content},
            "done": True,
            **self._metrics(start_time, first_token_time, end_time, token_count),
        }

    def stop(self):
        # Deliberately not releasing self._vdevice here: it's the shared
        # HailoRT device (lib/hailo/device.py) used by Ears' Whisper engine
        # too, so this client must not tear it down on its own.
        if self._llm is not None:
            self._llm.clear_context()
            self._llm.release()
            self._llm = None
