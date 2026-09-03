import os
import re
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional, Union

from lib.Threads import Process
from models.llm.classifier import build_conversation_classifier_prompt
from models.llm.identity import build_identity_system_prompt

# Path configuration
LIB_PATH = Path(__file__).parent.resolve()
PROJECT_ROOT = LIB_PATH.parent

# Which backend to talk to for LLM inference: 'ollama' or 'hailo'.
LLM_ENGINE = os.getenv("LLM_ENGINE", "ollama").strip().lower()

class Mind:
    def __init__(
            self,
            conversation_history_length: int = 4,
            debug: bool = False,
        ):

        self._debug = debug
        self._is_ready = False

        if LLM_ENGINE == "hailo":
            from lib.hailo.client import HailoClient
            from models.llm.config.hailo import (
                get_classifier_model_options,
                get_conversation_model_options,
                get_model_config,
            )

            config = get_model_config()
            self.model_name = config["model_hef"]
            self.client = HailoClient()
        else:
            from lib.ollama.client import OllamaClient
            from models.llm.config.ollama import (
                get_classifier_model_options,
                get_conversation_model_options,
                get_model_config,
            )

            config = get_model_config()
            self.model_name = config["model_name"]
            self.client = OllamaClient(host=config["host"])

        self._get_conversation_model_options = get_conversation_model_options
        self._get_classifier_model_options = get_classifier_model_options

        self.system_prompt = build_identity_system_prompt()

        self.load_model(model=self.model_name)

        # Context history
        self.history_limit = conversation_history_length
        self.history = []

        # Runs think() in the background so callers (e.g. the brain-tick loop)
        # aren't blocked for the duration of a (possibly streamed) generation.
        self._think_process = Process()

        # Tracks in-flight requests (think()/classify_conversation(), including
        # ones fired from ad-hoc background threads elsewhere) so stop() can
        # wait for them to finish before tearing down the client/device -
        # releasing it out from under an active generation corrupts the
        # underlying connection (seen as HailoRT communication-closed errors).
        self._active_requests = 0
        self._active_requests_lock = threading.Lock()
        self._idle_event = threading.Event()
        self._idle_event.set()

        while not self._is_ready:
            time.sleep(0.5)

    def load_model(self, model):
        """Pull the given base model via the client and mark the runtime ready."""
        try:
            self.client.load_model(model)
            self._is_ready = True
        except Exception as exc:
            self._is_ready = False
            print(f"[Error] Could not load base model '{model}': {exc}")
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

        self.system_prompt = build_identity_system_prompt()

        messages: List[dict] = [
            {"role": "system", "content": self.system_prompt},
        ]

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
    _SENTENCE_BREAK_CHARS = set(".!?:;")

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

    def classify_conversation(self, text: Optional[str] = None) -> Optional[float]:
        """Classify whether an STT fragment was addressed to the robot.

        Returns:
            1.0 = ADDRESSED
            0.5 = AMBIGUOUS
            0.0 = NOT_ADDRESSED
            None = classification could not be parsed
        """

        request = (
            text
            or (self.history[-1].get("content", "") if self.history else "")
        ).strip()

        if not request:
            print("[Robot] Analyze skipped: empty STT fragment")
            return None

        options = self._get_classifier_model_options()
        prompt = build_conversation_classifier_prompt(request)
        started_at = time.perf_counter()

        self._begin_request()
        try:
            response = self.client.chat(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                options=options,
                logprobs=True,
            )

            raw_response = ""
            final_chunk = {}
            for chunk in response:
                content = (chunk.get("message", {}) or {}).get("content", "")
                if content:
                    raw_response += content
                if chunk.get("done", False):
                    final_chunk = chunk

            raw_response = raw_response.strip()
            elapsed_seconds = time.perf_counter() - started_at

            # ---------------------------------------------------------
            # Parse classification
            # ---------------------------------------------------------

            classification = None

            normalized_response = raw_response.upper()

            if normalized_response.startswith("ADDRESSED"):
                classification = "ADDRESSED"

            elif normalized_response.startswith("NOT_ADDRESSED"):
                classification = "NOT_ADDRESSED"

            elif normalized_response.startswith("AMBIGUOUS"):
                classification = "AMBIGUOUS"

            # ---------------------------------------------------------
            # Map classification directly to score
            # ---------------------------------------------------------

            if classification == "ADDRESSED":
                score = 1.0

            elif classification == "AMBIGUOUS":
                score = 0.5

            elif classification == "NOT_ADDRESSED":
                score = 0.0

            else:
                score = None

            # ---------------------------------------------------------
            # Timing
            # ---------------------------------------------------------

            api_time = final_chunk.get("total_duration", 0) / 1e9

            score_text = (
                f"{score:.1f}"
                if score is not None
                else "unavailable"
            )

            classification_text = (
                classification
                if classification is not None
                else "unparsed"
            )

            # ---------------------------------------------------------
            # Logging
            # ---------------------------------------------------------

            if self._debug:
                print(
                    f"[Robot] Analyze request: {request}"
                )

                print(
                    f"[Robot] Analyze response: "
                    f"{raw_response!r}"
                )

                print(
                    f"[Robot] Analyze classification: "
                    f"{classification_text}"
                )

                print(
                    f"[Robot] Analyze score: "
                    f"{score_text}"
                )

                print(
                    f"[Robot] Analyze response time: "
                    f"{elapsed_seconds:.3f}s "
                    f"(API: {api_time:.3f}s)"
                )

            return score

        except Exception as exc:
            elapsed_seconds = time.perf_counter() - started_at

            print(
                f"[Robot] Analyze request: {request}"
            )

            print(
                f"[Robot] Analyze failed after "
                f"{elapsed_seconds:.3f}s: {exc}"
            )

            return None
        finally:
            self._end_request()

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

        # Wait for any in-flight think()/classify_conversation() call to
        # finish before releasing the client - tearing down the underlying
        # connection/device while it's still mid-generation corrupts it
        # (e.g. HailoRT communication-closed / stream-not-activated errors).
        if not self._idle_event.wait(timeout=5.0):
            print("[Mind] Warning: stopping with a request still in flight.")

        self.client.stop()

    def __enter__(self): return self
    def __exit__(self, *args): self.stop()