import os
import psutil
import re
import subprocess
import time
import signal
import ollama
from dotenv import load_dotenv
from pathlib import Path
from typing import Optional

# Path configuration
LIB_PATH = Path(__file__).parent.resolve()
PROJECT_ROOT = LIB_PATH.parent
OLLAMA_PATH = LIB_PATH / "ollama" / "dist"
MODELS_PATH = LIB_PATH / "ollama" / "models"
OLLAMA_BIN = OLLAMA_PATH / "bin" / "ollama"
LOGS_PATH = OLLAMA_PATH / "server.log"
MODELFILE_PATH = PROJECT_ROOT / "personality.modelfile"

BASE_URL = "http://localhost:11434"

class LLMService:
    def __init__(self):
        load_dotenv()
        
        # Identity settings
        self.base_model = os.getenv("OLLAMA_BASE_MODEL", "gemma3:270m")
        self.model_name = os.getenv("OLLAMA_MODEL_NAME", "pip")
        self.system_prompt = os.getenv("OLLAMA_SYSTEM_PROMPT", "You are Robot.")
        
        self.process = None
        self.client = ollama.Client(host=BASE_URL)

        # Hardware profile for RPi5
        self.options = {
            "num_ctx": int(os.getenv("OLLAMA_CONTEXT_LENGTH", 1024)),
            "num_thread": int(os.getenv("OLLAMA_THREADS", 4)),
            "temperature": float(os.getenv("OLLAMA_TEMPERATURE", 0.8)),
            "num_predict": int(os.getenv("OLLAMA_NUM_PREDICT", 40)),
            "stop": ["User:", "Pip:"]
        }

        self._prepare_environment()
        self._force_stop_server()
        self.start_server()
        self.load_model()

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
        """Creates the 'pip' model with a simple dot-trail progress indicator."""
        print(f"[Robot] Initializing personality for '{self.model_name}', using {self.base_model}", end="", flush=True)
        
        try:
            stream = self.client.create(
                model=self.model_name,
                from_=self.base_model,
                system=self.system_prompt,
                parameters=self.options,
                stream=True 
            )

            for chunk in stream:
                # Every time we get a progress update with data, print a dot
                if 'completed' in chunk:
                    print(".", end="", flush=True)
                
                # If the status changes (e.g., from 'pulling' to 'verifying'), 
                # you can optionally print the new status on a new line
                status = chunk.get('status', '')
                if status == "success":
                    print("\n[-] Personality locked in.")
                    return

        except Exception as e:
            print(f"\n[Error] Could not build personality model: {e}")


    def think(self, prompt: str) -> Optional[str]:
        if not prompt: return None
        try:
            start_time = time.perf_counter()
            # Note: num_thread is already in your Modelfile, no need to pass here
            response = self.client.generate(model=self.model_name, prompt=prompt, stream=False)
            
            duration = time.perf_counter() - start_time
            print(f"[Robot] Response received in {duration:.2f}s")
            return self._response_format(response['response'])
        
        except Exception as e:
            print(f"[Critical] Brain error: {e}")
            return None
        
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