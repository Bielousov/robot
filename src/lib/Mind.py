import os
import re
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional, Union

from lib.Threads import Process

# Path configuration
LIB_PATH = Path(__file__).parent.resolve()
PROJECT_ROOT = LIB_PATH.parent

class Mind:
    def __init__(
            self,
            conversation_history_length: int = 4,
            debug: bool = False,
        ):

        self._debug = debug
        self._is_ready = False

        from lib.ollama.client import OllamaClient
        from models.ollama.config.ollama import get_model_config

        # Mind only ever runs Ollama on the RPi CPU, against the
        # trained/personality model (src/models/ollama/train.sh, registered
        # under OLLAMA_MODEL_NAME) - there is no base-model fallback and no
        # other backend. Its Modelfile already carries the right generation
        # parameters and a baked-in SYSTEM prompt, so nothing here overrides
        # them: no conversation options are sent
        # (self._get_conversation_model_options returns {}), and no separate
        # text system prompt is built or sent (an explicit system message,
        # even an empty one, would override the Modelfile's own SYSTEM
        # directive instead of adding to it).
        config = get_model_config()
        self.model_name = config["model_name"]
        self.client = OllamaClient(host=config["host"])
        self._get_conversation_model_options = lambda: {}
        self.system_prompt = ""

        self._load_model(model=self.model_name)

        # Context history
        self.history_limit = conversation_history_length
        self.history = []

        # Runs think() in the background so callers (e.g. the brain-tick loop)
        # aren't blocked for the duration of a (possibly streamed) generation.
        self._think_process = Process()

        # Tracks in-flight requests (think(), including ones fired from
        # ad-hoc background threads elsewhere) so stop() can wait for them
        # to finish before tearing down the client/device.
        self._active_requests = 0
        self._active_requests_lock = threading.Lock()
        self._idle_event = threading.Event()
        self._idle_event.set()

        while not self._is_ready:
            time.sleep(0.5)
    
    def _load_model(self, model):
        """Load the given model via the client and mark the runtime ready."""
        try:
            self.client.load_model(model)
            self._is_ready = True
        except Exception as exc:
            self._is_ready = False
            print(f"[Error] Could not load model '{model}': {exc}")
            raise

    def _begin_request(self):
        with self._active_requests_lock:
            self._active_requests += 1
            self._idle_event.clear()

    def _end_request(self):
        with self._active_requests_lock:
            self._active_requests = max(0, self._active_requests - 1)
            if self._active_requests == 0:
                self._idle_event.set()

    def _build_request_messages(
        self,
        prompts: List[str],
        context: Optional[List[str]] = None,
    ) -> List[dict]:
        """Build a simple conversation transcript mirroring the web app.

        Recent actual history goes first, followed by the latest user message.
        Context is kept minimal and appended as a plain note; no synthetic prompt
        wrappers are injected because they alter the model behavior.
        """
        final_prompt = prompts[-1].strip() if prompts and prompts[-1] else ""
        if not final_prompt:
            return []

        # self.system_prompt is always empty (set once in __init__): Ollama's
        # trained model carries its own SYSTEM directive in its Modelfile, and
        # an explicit system message here, even an empty one, would override
        # it rather than adding to it.
        messages = [{"role": "system", "content": self.system_prompt}] if self.system_prompt else []

        recent_history = self.history[-self.history_limit:] if self.history else []
        for entry in recent_history:
            content = (entry.get("content") or "").strip()
            if not content:
                continue
            messages.append({
                "role": entry.get("role", "user"),
                "content": content,
            })

        if context:
            compact_context = " | ".join(
                str(item).strip()
                for item in context
                if str(item).strip()
            )
            if compact_context:
                messages.append({
                    "role": "user",
                    "content": f"Context: {compact_context}",
                })

        prompt_lower = final_prompt.lower()
        asks_about_context = any(
            keyword in prompt_lower
            for keyword in [
                "time",
                "date",
                "day",
                "sensor",
                "temperature",
                "battery",
                "location",
                "where are you",
                "what time",
                "what date",
                "status",
                "environment",
                "weather",
            ]
        )

        if asks_about_context:
            runtime_context = self._generate_prompt_context()
            if runtime_context:
                messages.append({
                    "role": "user",
                    "content": f"Context: {runtime_context}",
                })

        messages.append({
            "role": "user",
            "content": final_prompt,
        })

        return messages

    def think(
        self,
        prompt: Union[str, List[str]],
        callback: Optional[Callable[[Optional[str], Optional[Exception], bool], None]] = None,
        context: Optional[List[str]] = None,
        stream: bool = True,
    ) -> None:
        """Kick off a (possibly streamed) chat completion on a background thread.

        Results are only available via `callback`; this returns immediately.
        """
        self._think_process.run(self._think, prompt, callback, context, stream)

    def _think(
        self,
        prompt: Union[str, List[str]],
        callback: Optional[Callable[[Optional[str], Optional[Exception], bool], None]] = None,
        context: Optional[List[str]] = None,
        stream: bool = True,
    ) -> Optional[str]:

        # Normalize prompt to a list for consistent processing
        prompts = [prompt] if isinstance(prompt, str) else prompt

        if not prompts or all(not p for p in prompts):
            if callback:
                callback(None, ValueError("Empty prompt"), True)
            return None

        self._begin_request()
        try:
            current_prompt = prompts[-1].strip() if prompts[-1] else ""
            if not current_prompt:
                if callback:
                    callback(None, ValueError("Empty prompt"), True)
                return None

            messages = self._build_request_messages(prompts, context=context)
            options = self._get_conversation_model_options()

            response = self.client.chat(
                messages=messages,
                options=options,
                stream=stream,
            )

            if stream:
                answer = self._consume_stream(response, callback)
            else:
                if self._debug:
                    self._response_metrics(response)
                
                answer = self._response_format(response['message']['content'])
                if callback:
                    callback(answer, None, True)

            # Persist only the actual completed turn after the model responds.
            self.add_to_history('user', current_prompt)
            self.add_to_history('robot', answer)

            return answer

        except Exception as e:
            print(f"[Critical] Brain error: {e}")

            if callback:
                callback(None, e, True)

            return None
        finally:
            self._end_request()

    # Chunks handed to callback are buffered up to (and including) one of
    # these, so consumers like Voice get whole clauses instead of single
    # tokens/words.
    _SENTENCE_BREAK_CHARS = set(".!?:;…")

    def _consume_stream(
        self,
        response_stream,
        callback: Optional[Callable[[Optional[str], Optional[Exception], bool], None]],
    ) -> str:
        """Consume a streamed chat response, invoking callback once per clause.

        callback is called as (text, error, done): text carries a buffered
        chunk up to (and including) the first punctuation mark found since the
        last flush (or None if nothing new to flush, such as the final chunk
        with no trailing text), done is True only for the final chunk once the
        whole answer has arrived.
        """
        answer_parts = []
        final_chunk = None
        buffer = ""

        started_at = time.perf_counter()
        first_token_at = None

        for chunk in response_stream:
            content = (chunk.get('message', {}) or {}).get('content', '')
            if content:
                if first_token_at is None:
                    first_token_at = time.perf_counter()
                answer_parts.append(content)
                buffer += content

            done = bool(chunk.get('done', False))
            if done:
                final_chunk = chunk

            split_at = next(
                (i for i, ch in enumerate(buffer) if ch in self._SENTENCE_BREAK_CHARS),
                None,
            )
            while split_at is not None:
                piece, buffer = buffer[:split_at + 1], buffer[split_at + 1:]
                if callback:
                    callback(piece, None, False)
                split_at = next(
                    (i for i, ch in enumerate(buffer) if ch in self._SENTENCE_BREAK_CHARS),
                    None,
                )

            if done and callback:
                callback(buffer or None, None, True)

        if final_chunk is not None:
            ttft = (first_token_at - started_at) if first_token_at is not None else None
            if self._debug:
                self._response_metrics(final_chunk, ttft=ttft)

        return self._response_format("".join(answer_parts))

    def add_to_history(self, role: str, message: str) -> list:
        """
        Appends a message to context and maintains the sliding window.
        Returns the updated history list.
        """
        if not message:
            return self.history

        # 1. Append the new interaction
        self.history.append({'role': role, 'content': message})

        # 2. Enforce the sliding window (FIFO)
        # We keep the most recent 'history_limit' messages
        if len(self.history) > self.history_limit:
            self.history = self.history[-self.history_limit:]
            
        return self.history
    
    def clear_history(self):
        """Reset Pip's short-term memory."""
        if self._debug:
            print("[Robot] Memory banks cleared.")
        self.history = []

    def _generate_prompt_context(self):
        """Return a compact, factual sensor/runtime context line for the current turn.

        This is intentionally tiny and plain-text so the model sees useful facts
        (date/time/location/etc.) without it sounding like a generic assistant or
        a system prompt block.
        """
        now = datetime.now()
        return (
            f"date={now.strftime('%Y-%m-%d')}, "
            f"time={now.strftime('%H:%M')}, "
            f"location={os.getenv('CONTEXT_LOCATION', 'Planet Earth')}, "
            f"language={os.getenv('LANGUAGE', 'English')}"
        )

    def _response_format(self, text: str) -> str:
        """
        Scrubs emojis and Markdown bold symbols to maintain 
        Pip's cold, ASCII-only aesthetic.
        """
        if not text:
            return ""

        # 1. Remove Markdown bold/italic symbols (e.g., **text** or *text*)
        # We replace the asterisks with an empty string
        clean_text = text.replace("*", "")

        # 2. Remove Emojis and non-ASCII symbols
        # This regex looks for any character that isn't a standard 
        # printable ASCII character (letters, numbers, punctuation)
        clean_text = re.sub(r'[^\x00-\x7F]+', '', clean_text)

        # 3. Clean up extra whitespace/newlines
        clean_text = " ".join(clean_text.split())

        return clean_text.strip()
    
    def _response_metrics(self, response, ttft: Optional[float] = None):
        # Ollama returns these in nanoseconds
        total_dur = response.get('total_duration', 0) / 1e9
        # Time spent loading the model into the GPU/RAM.
        load_dur = response.get('load_duration', 0) / 1e9
        # Time spent evaluating the prompt, before generation starts.
        prompt_eval_dur = response.get('prompt_eval_duration', 0) / 1e9
        # Time spent "writing" the response.
        eval_dur = response.get('eval_duration', 0) / 1e9

        # Throughput: tokens per second
        eval_count = response.get('eval_count', 1)
        tps = eval_count / eval_dur if eval_dur > 0 else 0

        # Time to first token: measured directly while streaming when available,
        # otherwise approximated from the load + prompt-eval phases.
        if ttft is None:
            ttft = load_dur + prompt_eval_dur

        print(f"[Robot] Response: {eval_count} tokens | {tps:.2f} tokens/s")
        print(
            f"[Robot] Timings: Total {total_dur:.2f}s "
            f"(TTFT: {ttft:.2f}s, Load: {load_dur:.2f}s, Eval: {eval_dur:.2f}s)"
        )
    
    def stop(self):
        self._think_process.stop()

        # Wait for any in-flight think() call to finish before this object
        # goes away.
        if not self._idle_event.wait(timeout=5.0):
            print("[Mind] Warning: stopping with a request still in flight.")

    def __enter__(self): return self
    def __exit__(self, *args): self.stop()