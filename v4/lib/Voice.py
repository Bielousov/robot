import subprocess
import os
import threading
from pathlib import Path
from .Threads import Process

LIB_PATH = Path(__file__).parent.resolve()
PIPER_DIR = LIB_PATH / "piper"
VOICE_DIR = PIPER_DIR / "voices"
PIPER_BIN = PIPER_DIR / "dist/piper"

class Voice:
    def __init__(self, voice_model_name="en_US-danny-low.onnx", voice_sample_rate=22050):
        self.__process = Process()
        self._format = "S16_LE"
        self._niceness = 10
        self._threads = 2
        
        self._model_path = VOICE_DIR / f"{voice_model_name}.onnx"
        self._sample_rate = voice_sample_rate
        
        # Audio lock prevents multiple 'say' calls from overlapping
        self._speech_lock = threading.Lock()
        
        if PIPER_BIN.exists():
            os.chmod(PIPER_BIN, 0o755)
        else:
            print(f"[Voice Warning]: Piper binary not found at {PIPER_BIN}")

    def say(self, text, callback=None):
        """Public method: Starts a background thread to speak."""
        threading.Thread(
            target=self._threaded_execution, 
            args=(text, callback), 
            daemon=True
        ).start()

    def _threaded_execution(self, text, callback):
        """Internal helper that manages the lock and subprocess."""
        with self._speech_lock:
            clean_text = text.replace('"', '\\"')
            command = (
                f'echo "{clean_text}" | '
                f'nice -n {self._niceness} "{PIPER_BIN}" '
                f'--model "{self._model_path}" '
                f'--threads {self._threads} '
                f'--output_raw | '
                f'aplay -r {self._sample_rate} -f {self._format} -t raw'
            )
            
            try:
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