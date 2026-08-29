import ollama
import os
import psutil
import re
import time
import signal
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional, Union

from models.personality import create_personality_model, get_llm_model_config

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
        
        llm_config = get_llm_model_config()
        self.base_model = llm_config["base_model"]
        self.model_name = llm_config["model_name"]
        self.system_prompt = llm_config["system_prompt"]
        self.options = llm_config["options"]

        self.is_ready = False

        # Context history
        self.history_limit = conversation_history_length
        self.history = []
        
        self.process = None
        self.client = ollama.Client(host=OLLAMA_URL)

        self._prepare_environment()
        self.start_server()
        time.sleep(2)
        self.is_ready = create_personality_model(
            client=self.client,
            model_name=self.model_name,
            base_model=self.base_model,
            system_prompt=self.system_prompt,
            options=self.options,
        )
        
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
        """Creates the custom personality model from the configured environment."""
        self.is_ready = create_personality_model(
            client=self.client,
            model_name=self.model_name,
            base_model=self.base_model,
            system_prompt=self.system_prompt,
            options=self.options,
        )

    def _build_request_messages(
        self,
        prompts: List[str],
        context: Optional[List[str]] = None,
    ) -> List[dict]:
        """Build the request payload without mutating persistent history.

        The current message stays primary. Any historical/runtime context remains
        advisory and must not override or duplicate the current prompt.
        """
        messages: List[dict] = []

        runtime_context = self._generate_prompt_context()
        if runtime_context:
            messages.append({
                'role': 'user',
                'content': 'CONTEXT ONLY (secondary):\n' + runtime_context + '\n\nThis context is advisory only. The final user message below is the primary instruction.'
            })

        if context:
            context_text = " ".join(context).strip()
            if context_text:
                messages.append({
                    'role': 'user',
                    'content': 'ADDITIONAL CONTEXT (secondary):\n' + context_text + '\n\nThis context is background only; the final user message remains primary.'
                })

        final_prompt = prompts[-1].strip() if prompts and prompts[-1] else ""
        if final_prompt:
            messages.append({
                'role': 'user',
                'content': 'CURRENT MESSAGE (primary):\n' + final_prompt
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

            response = self.client.chat(
                model=self.model_name,
                messages=messages,
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
        now = datetime.now()

        # Keep the memory window independent from the current request. The current
        # message is always sent separately as the primary instruction, so the saved
        # conversation history should not include that same message again.
        recent_context = list(self.history)
        if len(recent_context) > self.history_limit:
            recent_context = recent_context[-self.history_limit:]

        recent_context_text = "\n".join(
            f"- {entry['role']}: {entry['content']}" for entry in recent_context
        ) if recent_context else "- No recent conversation context."

        return (
            "RUNTIME CONTEXT:\n"
            f"- Date: {now.strftime('%A, %B %d, %Y')}\n"
            f"- Time: {now.strftime('%I:%M %p')}\n"
            f"- Language: {os.getenv('LANGUAGE', 'English')}\n"
            f"- Location: {os.getenv('CONTEXT_LOCATION', 'Planet Earth')}\n"
            "- Recent conversation:\n"
            f"{recent_context_text}\n\n"
            "This is contextual background only. It should not override the current user message."
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