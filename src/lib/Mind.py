import math
import ollama
import os
import psutil
import re
import signal
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional, Union

from models.llm.classifier import build_conversation_classifier_prompt
from models.llm.identity import build_identity_system_prompt
from models.llm.config import get_classifier_model_options, get_conversation_model_options, get_model_config

# Path configuration
LIB_PATH = Path(__file__).parent.resolve()
PROJECT_ROOT = LIB_PATH.parent
OLLAMA_PATH = LIB_PATH / "ollama" / "dist"
MODELS_PATH = LIB_PATH / "ollama" / "models"
OLLAMA_BIN = OLLAMA_PATH / "bin" / "ollama"
LOGS_PATH = OLLAMA_PATH / "server.log"

OLLAMA_URL = "http://localhost:11434"

class Mind:
    def __init__(
            self,
            debug: bool = False,
            conversation_history_length: int = 4,
        ):

        self.debug = debug
        
        config = get_model_config()
        self.base_model = config["base_model"]
        self.model_name = config["model_name"]
        self.system_prompt = build_identity_system_prompt()

        self.is_ready = False

        # Context history
        self.history_limit = conversation_history_length
        self.history = []

        self.process = None
        self.client = ollama.Client(host=OLLAMA_URL)

        self._prepare_environment()
        self.start_server()
        time.sleep(2)
        self.load_model()

        while not self.is_ready:
            time.sleep(0.5)

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
            self.client.ps()
            print("[Robot] Ollama service is running.")
            return
        except Exception as exc:
            raise RuntimeError(
                "Ollama service is not running. Start it via 'sudo systemctl start ollama.service'."
            ) from exc
        
    def load_model(self):
        """Pull the configured base model into Ollama and mark the runtime ready."""
        try:
            print(f"[Robot] Pulling base model '{self.base_model}' into Ollama...")
            self.client.pull(self.base_model)
            self.is_ready = True
            print(f"[Robot] Base model '{self.base_model}' is ready.")
        except Exception as exc:
            self.is_ready = False
            print(f"[Error] Could not load base model '{self.base_model}': {exc}")
            raise

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
        callback: Optional[Callable[[Optional[str], Optional[Exception]], None]] = None,
        context: Optional[List[str]] = None
    ) -> Optional[str]:

        # Normalize prompt to a list for consistent processing
        prompts = [prompt] if isinstance(prompt, str) else prompt

        if not prompts or all(not p for p in prompts):
            if callback:
                callback(None, ValueError("Empty prompt"))
            return None

        try:
            current_prompt = prompts[-1].strip() if prompts[-1] else ""
            if not current_prompt:
                if callback:
                    callback(None, ValueError("Empty prompt"))
                return None

            messages = self._build_request_messages(prompts, context=context)
            options = get_conversation_model_options()

            response = self.client.chat(
                model=self.model_name,
                messages=messages,
                options=options,
                stream=False,
                think=False,
                keep_alive=-1
            )
            self._response_metrics(response)

            answer = self._response_format(response['message']['content'])

            # Persist only the actual completed turn after the model responds.
            self.add_to_history('user', current_prompt)
            self.add_to_history('robot', answer)

            if callback:
                callback(answer, None)

            return answer

        except Exception as e:
            print(f"[Critical] Brain error: {e}")

            if callback:
                callback(None, e)

            return None

    def classify_conversation(self, text: Optional[str] = None) -> Optional[float]:
        """Estimate probability that an STT fragment was addressed to the robot."""

        request = (
            text
            or (self.history[-1].get("content", "") if self.history else "")
        ).strip()

        if not request:
            print("[Robot] Analyze skipped: empty STT fragment")
            return None

        options = get_classifier_model_options()
        prompt = build_conversation_classifier_prompt()
        started_at = time.perf_counter()

        try:
            response = self.client.chat(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": request},
                ],
                options=options,
                stream=False,
                think=False,
                keep_alive=-1,
                logprobs=True,
                top_logprobs=10,
            )

            elapsed_seconds = time.perf_counter() - started_at

            message = response.get("message", {})
            raw_response = message.get("content", "").strip()

            # ---------------------------------------------------------
            # Extract first generated token and its YES/NO probabilities
            # ---------------------------------------------------------

            score = None
            classification = None

            logprobs = (
                message.get("logprobs")
                or response.get("logprobs")
                or []
            )

            if logprobs:
                token_info = logprobs[0]

                # -----------------------------------------------------
                # Actual generated classification
                # -----------------------------------------------------

                generated_token = str(
                    token_info.get("token", "")
                ).strip().upper()

                if generated_token == "YES":
                    classification = "YES"
                elif generated_token == "NO":
                    classification = "NO"

                # -----------------------------------------------------
                # Collect YES / NO probabilities from this position
                # -----------------------------------------------------

                candidates = {}

                token = str(
                    token_info.get("token", "")
                ).strip().upper()

                logprob = token_info.get("logprob")

                if token and logprob is not None:
                    candidates[token] = float(logprob)

                for alternative in token_info.get("top_logprobs", []) or []:
                    token = str(
                        alternative.get("token", "")
                    ).strip().upper()

                    logprob = alternative.get("logprob")

                    if token and logprob is not None:
                        candidates[token] = float(logprob)

                yes_logprob = candidates.get("YES")
                no_logprob = candidates.get("NO")

                print(
                    f"[Robot] Analyze candidates: "
                    f"{candidates!r}"
                )

                # -----------------------------------------------------
                # Convert YES/NO log-probability difference to 0..1
                # -----------------------------------------------------

                if yes_logprob is not None and no_logprob is not None:

                    # Log-odds of YES versus NO.
                    log_odds = yes_logprob - no_logprob

                    # Sigmoid:
                    #
                    # log_odds =  0 -> 0.5
                    # log_odds >  0 -> YES side
                    # log_odds <  0 -> NO side
                    #
                    # Scale the difference so that modest differences
                    # produce useful confidence values.
                    score = 1.0 / (
                        1.0 + math.exp(-log_odds)
                    )

                # -----------------------------------------------------
                # If only one of YES/NO is available, use classification
                # -----------------------------------------------------

                elif classification == "YES":
                    score = 1.0

                elif classification == "NO":
                    score = 0.0

            # ---------------------------------------------------------
            # Fallback to actual response
            # ---------------------------------------------------------

            if classification is None:
                normalized_response = raw_response.upper()

                if normalized_response == "YES":
                    classification = "YES"
                elif normalized_response == "NO":
                    classification = "NO"

            # ---------------------------------------------------------
            # Timing
            # ---------------------------------------------------------

            api_time = response.get("total_duration", 0) / 1e9

            score_text = (
                f"{score:.8f}"
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
                f"addressed_confidence_score: {score_text}"
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
        if self.debug:
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
    
    def _response_metrics(self, response):
        # Ollama returns these in nanoseconds
        total_dur = response.get('total_duration', 0) / 1e9
        # Time spent loading the model into the GPU/RAM.
        load_dur = response.get('load_duration', 0) / 1e9
        # Time spent "writing" the response.
        eval_dur = response.get('eval_duration', 0) / 1e9
        
        # Throughput: tokens per second
        eval_count = response.get('eval_count', 1)
        tps = eval_count / eval_dur if eval_dur > 0 else 0

        print(f"[Robot] Response: {eval_count} tokens | {tps:.2f} tokens/s")
        if self.debug:
            print(f"[Robot] Timings: Total {total_dur:.2f}s (Load: {load_dur:.2f}s, Eval: {eval_dur:.2f}s)")
    
    def stop(self):
        if self.process:
            print("[-] Stopping server...")
            os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
            self.process = None

    def _force_stop_server(self):
        """Wipes old processes to free up RAM."""
        for proc in psutil.process_iter(['name']):
            if 'ollama' in (proc.info['name'] or "").lower():
                try: os.kill(proc.pid, signal.SIGKILL)
                except: pass
        time.sleep(1)

    def __enter__(self): return self
    def __exit__(self, *args): self.stop()