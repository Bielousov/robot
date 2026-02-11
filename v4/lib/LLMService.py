import os
import psutil
import re
import subprocess
import time
import signal
import sys
import ollama
from dotenv import load_dotenv
from pathlib import Path
from typing import Callable, List, Optional, Union

# Path configuration
LIB_PATH = Path(__file__).parent.resolve()
PROJECT_ROOT = LIB_PATH.parent
OLLAMA_PATH = LIB_PATH / "ollama" / "dist"
MODELS_PATH = LIB_PATH / "ollama" / "models"
OLLAMA_BIN = OLLAMA_PATH / "bin" / "ollama"
LOGS_PATH = OLLAMA_PATH / "server.log"

BASE_URL = "http://localhost:11434"

class LLMService:
    def __init__(self):
        load_dotenv()
        
        # Identity settings
        self.base_model = os.getenv("OLLAMA_BASE_MODEL", "gemma3:270m")
        self.model_name = os.getenv("OLLAMA_MODEL_NAME", "pip")
        self.system_prompt = os.getenv("OLLAMA_SYSTEM_PROMPT", "You are Robot.")

        self.is_ready = False

        # Context history
        self.history_limit = int(os.getenv("OLLAMA_HISTORY_LIMIT", 2))
        self.history = []
        
        self.process = None
        self.client = ollama.Client(host=BASE_URL)

        # Hardware profile for RPi5
        self.options = {
            # The maximum number of tokens the model can "remember" at once (history + system prompt + current input).
            "num_ctx": int(os.getenv("OLLAMA_CONTEXT_LENGTH", 1024)),

            # Number of CPU cores allocated for processing; higher can be faster, but too high causes system stutter.
            "num_thread": int(os.getenv("OLLAMA_THREADS", 4)),

            # Controls randomness: 0.0 is deterministic/robotic, 1.0+ is creative/chaotic. (Lower is better for Pip).
            "temperature": float(os.getenv("OLLAMA_TEMPERATURE", 1.0)),

            # The maximum length of the generated response in tokens; prevents the model from rambling.
            "num_predict": int(os.getenv("OLLAMA_NUM_PREDICT", 40)),

            # Discourages the model from repeating words or phrases; helps prevent Pip from getting stuck in a loop.
            "repeat_penalty": float(os.getenv("OLLAMA_REPEAT_PENALTY", 1.2)),

            # Quality filter: Limits the model's word choices to the 'K' most likely next words.
            "top_k": float(os.getenv("OLLAMA_TOP_K", 40)),  # Limits vocabulary to the most likely "efficient" words
            
            # Probability filter: Only considers words whose combined probability reaches 'P' (Nucleus sampling).
            "top_p": float(os.getenv("OLLAMA_TOP_P", 0.9)),
            
            "stop": ["User:", "Pip:"]
        }

        self._prepare_environment()
        self._force_stop_server()
        self.start_server()
        self.load_model()
        self._wait_until_ready()

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
        """Starts Ollama background process."""
        try:
            self.client.ps() 
            print("[Robot] Server already active.")
        except Exception:
            print("[Robot] Starting Ollama server...")
            log_file = open(LOGS_PATH, "a")
            self.process = subprocess.Popen(
                [str(OLLAMA_BIN), "serve"],
                stdout=log_file, stderr=log_file,
                env=os.environ, preexec_fn=os.setsid 
            )
            
            # Health check loop
            for _ in range(15):
                time.sleep(1)
                try:
                    self.client.ps()
                    return
                except: continue
            raise RuntimeError("Ollama failed to start. Check server.log")
        
    def load_model(self):
        """Creates the 'pip' model showing: Loading model [name] ([size] MB): [percent] %"""
        print(f"[Robot] Initializing personality for '{self.model_name}' based on {self.base_model} model")
        
        try:
            stream = self.client.create(
                model=self.model_name,
                from_=self.base_model,
                system=self.system_prompt,
                parameters=self.options,
                stream=True 
            )

            for chunk in stream:
                status = chunk.get('status', '')
                completed = chunk.get('completed')
                total = chunk.get('total')

                if total and completed and total > 0:
                    total_mb = total / (1024 * 1024)
                    loaded_pct = (completed / total) * 100
                    
                    # Format: Loading model gemma3:1b (120.5 MB): 45.2 %
                    sys.stdout.write(
                        f"\rLoading model {self.base_model} ({total_mb:.1f} MB): {loaded_pct:.1f} %"
                    )
                    sys.stdout.flush()
                elif status and status != "success":
                    # Print other statuses like 'verifying' or 'writing'
                    sys.stdout.write(f"\r{status}...{' ' * 20}")
                    sys.stdout.flush()

                if status == "success" or chunk.get('done'):
                    print(f"\n[-] Personality '{self.model_name}' locked in. Pip is online.")
                    self.is_ready = True
                    return
        except Exception as e:
            print(f"\n[Error] Could not build personality model: {e}")

    def think(
        self,
        prompt: Union[str, List[str]],
        callback: Optional[Callable[[Optional[str], Optional[Exception]], None]] = None
    ) -> Optional[str]:

        # Normalize prompt to a list for consistent processing
        prompts = [prompt] if isinstance(prompt, str) else prompt

        if not prompts or all(not p for p in prompts):
            if callback:
                callback(None, ValueError("Empty prompt"))
            return None

        messages = None
        for p in prompts:
            if p: # Ensure we don't send empty strings in the array
                messages = self.add_to_history('user', p)

        try:
            response = self.client.chat(
                model=self.model_name,
                messages=messages,
                stream=False,
                keep_alive=-1
            )
            self._response_metrics(response)
            
            answer = self._response_format(response['message']['content'])
            self.add_to_history('assistant', answer)

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
        print("[Robot] Memory banks cleared.")
        self.history = []

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

    def _wait_until_ready(self):
        while not self.is_ready:
            time.sleep(0.5)

    def __enter__(self): return self
    def __exit__(self, *args): self.stop()