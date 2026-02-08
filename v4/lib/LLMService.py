import httpx
import os
import psutil
import subprocess
import time
import signal
from dotenv import load_dotenv
from pathlib import Path
from typing import Optional

LIB_PATH = Path(__file__).parent.resolve()
OLLAMA_PATH = LIB_PATH / "ollama" / "dist"
MODELS_PATH = LIB_PATH / "ollama" / "models"
OLLAMA_BIN = OLLAMA_PATH / "ollama"
LOGS_PATH = OLLAMA_PATH / "server.log"

BASE_URL = "http://localhost:11434"

class LLMService:
    def __init__(self):

        # 1. Load ENV
        load_dotenv()

        # 2. Configuration from Environment (with your RPi5 defaults)
        self.model_name = os.getenv("OLLAMA_MODEL_NAME", "gemma3:1b")
        self.context_length = int(os.getenv("OLLAMA_CONTEXT_LENGTH", "1024"))
        self.threads = int(os.getenv("OLLAMA_THREADS", "4"))
        
        self.process = None
        self.client = httpx.Client(base_url=BASE_URL, timeout=120.0)

        self._prepare_environment()
        self._force_stop_server()
        self.start_server()
        self.load_model()

    def _prepare_environment(self):
        """Sets the specific RPi5 environment flags."""
        os.makedirs(OLLAMA_PATH, exist_ok=True)
        os.makedirs(MODELS_PATH, exist_ok=True)
        
        env_vars = {
            "OLLAMA_MODELS": str(MODELS_PATH),
            "OLLAMA_CONTEXT_LENGTH": str(self.context_length),
            "OLLAMA_FLASH_ATTENTION": "0",
            "OLLAMA_MAX_LOADED_MODELS": "1",
            "OLLAMA_MEMORY_FRACTION": "0.7",
            "OLLAMA_NUM_PARALLEL": "2",
            "OLLAMA_THREADS": str(self.threads),
            # "OLLAMA_NO_MMAP": "1",
            # "OLLAMA_NOPRUNE": "1",
            # "OLLAMA_LLM_LIBRARY": "cpu",
            # "OLLAMA_NUMA": "0"
        }
        os.environ.update(env_vars)

    def start_server(self):
        """Starts the Ollama server if not already running."""
        try:
            # Check if something is already on the port
            self.client.get("/api/version")
            print("[Robot] LLM server already running.")
        except httpx.ConnectError:
            print("[Robot] Waking up the LLM service...")
            log_file = open(LOGS_PATH, "a")
            self.process = subprocess.Popen(
                [str(OLLAMA_BIN), "serve"],
                stdout=log_file,
                stderr=log_file,
                preexec_fn=os.setsid # Create a process group for clean kill
            )
            
            # Wait for health check
            for _ in range(10):
                time.sleep(1)
                try:
                    if self.client.get("/api/version").status_code == 200:
                        print("[Robot] Server is online.")
                        return
                except httpx.ConnectError:
                    continue
            raise RuntimeError("LLM service failed to start. Check server.log")

    def load_model(self):
        """Ensures the specific model is loaded into memory."""
        print(f"[Robot] Loading model: {self.model_name}...")
        print(f"Loading models path {MODELS_PATH}")
        payload = {
            "model": self.model_name,
            "keep_alive": -1,
            "prompt": "",
            "stream": False,
            "options": {
                "num_ctx": self.context_length,
                "num_thread": self.threads
            }
        }
        try:
            # CHANGE: Changed endpoint from /api/create to /api/generate
            response = self.client.post("/api/generate", json=payload)
            
            if response.status_code == 200:
                print(f"[Robot] {self.model_name} is ready for prompts.")
            else:
                print(f"[Error] Failed to load model: {response.text}")
        except Exception as e:
            print(f"[Robot] Critical error during model load: {e}")

    def think(self, prompt: str) -> Optional[str]:
        """
        Sends a prompt to the model and returns the response string.
        Measures performance in seconds.
        """
        if not prompt:
            return None

        print(f"[Robot] Thinking about: {prompt[:50]}...")

        # Start high-precision timer
        start_time = time.perf_counter()

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,  # Set to True if you want to handle word-by-word
            "options": {
                "num_ctx": self.context_length,
                "num_thread": self.threads,
            }
        }

        try:
            response = self.client.post("/api/generate", json=payload)
            end_time = time.perf_counter()

            if response.status_code == 200:
                result = response.json()
                reply = result.get("response", "")
                
                # Performance metrics
                duration = end_time - start_time
                print(f"[Robot] Response received in {duration:.2f}s")
                
                return reply
            else:
                print(f"[Error] Inference failed: {response.text}")
                return None

        except Exception as e:
            print(f"[Critical] Failed to communicate with brain: {e}")
            return None
            
    def stop(self):
        """Forcefully kills the server and all its child runners."""
        if self.process and self.process.poll() is None:
            print("[-] Force-stopping the LLM service...")
            try:
                # Kill the entire process group (the minus sign is key!)
                os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                self.process.wait(timeout=5)
            except Exception as e:
                print(f"[!] Cleanup error: {e}")
            finally:
                self.process = None
                print("[-] LLM service stopped.")

    def _force_stop_server(self):
        """Pure Python pkill replacement to wipe out any existing Ollama processes."""
        print("[Robot] Evicting existing brain instances...")
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                # Check if 'ollama' is in name or command line
                name = proc.info['name'] or ""
                cmdline = " ".join(proc.info['cmdline'] or [])
                
                if 'ollama' in name.lower() or 'ollama' in cmdline.lower():
                    # Don't kill our current python script if it has 'ollama' in the path
                    if proc.info['pid'] == os.getpid():
                        continue
                        
                    print(f"[-] Killing process {proc.info['pid']}...")
                    os.kill(proc.info['pid'], signal.SIGKILL)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Short nap to let the OS release port 11434
        time.sleep(1.5)

    def __enter__(self):
        return self

    def __exit__(self):
        self.stop()

    def __del__(self):
        self.stop()

# Example usage:
if __name__ == "__main__":
    brain = LLMService()
    
    # Simple interaction loop
    question = "Generate a fictional quote that fits the most your character"
    answer = brain.think(question)
    
    if answer:
        print(f"\n[Pip]: {answer}\n")

    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass