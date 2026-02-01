import subprocess
import os
from pathlib import Path
from .Threads import Process

# --- Path Constants ---
# These are relative to the location of Voice.py (./v4/lib/)
LIB_PATH = Path(__file__).parent.absolute()
PIPER_DIR = LIB_PATH / "piper"
VOICE_DIR = PIPER_DIR / "voices"
PIPER_BIN = PIPER_DIR / "piper"

class Voice:
    def __init__(self, voice_model_name="en_US-lessac-medium.onnx"):
        self.__process = Process()
        
        # Resolve the specific model path
        self.model_path = VOICE_DIR / voice_model_name
        
        # Ensure the binary is executable
        if PIPER_BIN.exists():
            os.chmod(PIPER_BIN, 0o755)
        else:
            print(f"[Voice Warning]: Piper binary not found at {PIPER_BIN}")

    def say(self, text, callback=None):
        # Escape double quotes to prevent shell injection/errors
        clean_text = text.replace('"', '\\"')
        
        # Piper pipeline
        # aplay flags: -r (rate), -f (format), -t (type)
        command = (
            f'echo "{clean_text}" | '
            f'"{PIPER_BIN}" --model "{self.model_path}" --output_raw | '
            f'aplay -r 22050 -f S16_LE -t raw'
        )
        
        def _run():
            try:
                # shell=True enables the use of pipes (|)
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

        # Run via your Process thread wrapper
        self.__process.run(_run)