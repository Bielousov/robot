import os
import psutil
import re
import time
import signal
import ollama
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional, Union

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional runtime dependency
    def load_dotenv(*args, **kwargs):
        return False

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

from .MindProxy import OllamaAPIServer
from models.personality import create_personality_model, get_llm_model_config

# Path configuration
LIB_PATH = Path(__file__).parent.resolve()
PROJECT_ROOT = LIB_PATH.parent
OLLAMA_PATH = LIB_PATH / "ollama" / "dist"
MODELS_PATH = LIB_PATH / "ollama" / "models"
OLLAMA_BIN = OLLAMA_PATH / "bin" / "ollama"
LOGS_PATH = OLLAMA_PATH / "server.log"

BASE_URL = "http://localhost:11434"

class Mind:
    def __init__(
            self,
            debug: bool = False,
            conversation_history_length: int = 4,
        ):

        self.debug = debug

        # Ollama API server configuration
        ollama_proxy_port = int(os.getenv("OLLAMA_PROXY_PORT", 11435))
        self.api_server = OllamaAPIServer(proxy_port=ollama_proxy_port, ollama_base_url=BASE_URL)
        
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
        self.client = ollama.Client(host=BASE_URL)

        self._prepare_environment()
        self.start_server()
        self.api_server.start()
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
        
        # Inject overheard context as a system message if provided
        if context:
            context_str = "CONTEXT: " + " ".join(context)
            self.add_to_history('user', context_str)

            if self.debug:
                print(f"[Debug] Injected context into history: {context_str}")

        for p in prompts:
            if p: # Ensure we don't send empty strings in the array
                self.add_to_history('user', p)

                if self.debug:
                    print(f"[Debug] Added prompt to history: {p}")

        try:
            # Reintroduce just enough runtime context, but keep it as plain user text.
            # A system-style context block here can override the baked-in personality,
            # so we keep the identity in the model and only pass contextual hints.
            messages = []
            runtime_context = self._generate_prompt_context()
            if runtime_context:
                messages.append({'role': 'user', 'content': runtime_context})
            messages.append({'role': 'user', 'content': prompts[-1]})

            response = self.client.chat(
                model=self.model_name,
                messages=messages,
                stream=False,
                think=False,
                keep_alive=-1
            )
            self._response_metrics(response)
            
            answer = self._response_format(response['message']['content'])
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
        recent_context = self.history[-self.history_limit:] if self.history else []
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
            "Use this context only if it helps answer the current message."
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
        self.api_server.stop()
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