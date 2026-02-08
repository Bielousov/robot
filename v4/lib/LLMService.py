import os
import psutil
import subprocess
import time
import signal
import ollama  # Official Library
from dotenv import load_dotenv
from pathlib import Path
from typing import Optional

LIB_PATH = Path(__file__).parent.resolve()
OLLAMA_PATH = LIB_PATH / "ollama" / "dist"
MODELS_PATH = LIB_PATH / "ollama" / "models"
OLLAMA_BIN = OLLAMA_PATH / "bin" / "ollama"
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
        
        self._prepare_environment()
        
        self.process = None
        self.client = ollama.Client(host=BASE_URL)

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
            self.client.ps() 
            print("[Robot] LLM server already running.")
        except Exception:
            print("[Robot] Waking up the LLM service...")
            log_file = open(LOGS_PATH, "a")
            self.process = subprocess.Popen(
                [str(OLLAMA_BIN), "serve"],
                stdout=log_file,
                stderr=log_file,
                env=os.environ,
                preexec_fn=os.setsid 
            )
            
            # Wait for health check
            for _ in range(10):
                time.sleep(1)
                try:
                    self.client.ps()
                    print("[Robot] Server is online.")
                    return
                except Exception:
                    continue
            raise RuntimeError("LLM service failed to start. Check server.log")
    
    def load_model(self):
        """Checks if model exists locally; pulls it if missing."""
        try:
            self.client.show(self.model_name)
            print(f"[Robot] Model {self.model_name} found.")
        except ollama.ResponseError as e:
            if e.status_code == 404:
                print(f"[Robot] Pulling {self.model_name}... this may take a while.")
                self.client.pull(self.model_name)
            else:
                raise e

    def think(self, prompt: str) -> Optional[str]:
        if not prompt:
            return None

        print(f"[Robot] Thinking about: {prompt[:50]}...")

        # Define Pip's personality here
        messages = [
            {'role': 'system', 'content': 'You are Pip, a sophisticated robot.'},
            {'role': 'user', 'content': prompt}
        ]

        try:
            start_time = time.perf_counter()
            response = self.client.chat(
                model=self.model_name,
                messages=messages,
                options={"num_thread": self.threads}
            )
            end_time = time.perf_counter()
            print(f"[Robot] Response received in {(end_time - start_time):.2f}s")
            
            return response['message']['content']

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