import subprocess
import os
from pathlib import Path
from .Threads import Process

# --- Robust Path Resolution ---
# Path(__file__) is /home/pip/projects/robot/v4/lib/Voice.py
# .parent gets us to /home/pip/projects/robot/v4/lib/
LIB_PATH = Path(__file__).parent.resolve()

# Assets are anchored to this lib folder
PIPER_DIR = LIB_PATH / "piper"
VOICE_DIR = PIPER_DIR / "voices"
PIPER_BIN = PIPER_DIR / "piper"

class Voice:
    def __init__(self, voice_model_name="en_US-ryan-high.onnx"):
        self.__process = Process()
        
        # Specific model path
        self.model_path = VOICE_DIR / voice_model_name
        
        # Ensure the binary is executable
        if PIPER_BIN.exists():
            os.chmod(PIPER_BIN, 0o755)
        else:
            print(f"[Voice Warning]: Piper binary not found at {PIPER_BIN}")

    def say(self, text, callback=None):
        # Escape double quotes for shell safety
        clean_text = text.replace('"', '\\"')
        
        # Piper pipeline
        # -r 22050: Sampling rate for 'medium' voices
        # -f S16_LE: Signed 16-bit Little Endian raw audio
        command = (
            f'echo "{clean_text}" | '
            f'"{PIPER_BIN}" --model "{self.model_path}" --output_raw | '
            f'aplay -r 22050 -f S16_LE -t raw'
        )
        
        def _run():
            try:
                # shell=True handles the pipes (|) correctly
                process = subprocess.Popen(
                    command, 
                    shell=True, 
                    stdout=subprocess.DEVNULL, 
                    stderr=subprocess.DEVNULL
                )
                return_code = process.wait()

                if callback:
                    callback(success=(return_code == 0))

            except Exception as e:
                print(f"[Voice Error]: {e}")
                if callback:
                    callback(success=False, error=str(e))

        # Async execution via your Process thread wrapper
        self.__process.run(_run)