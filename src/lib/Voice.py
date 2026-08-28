import os
import subprocess
import threading
import atexit
import signal
from pathlib import Path
from typing import Callable, Optional

# Paths (Assuming same structure)
LIB_PATH = Path(__file__).parent.resolve() / "piper"
MODELS_PATH = LIB_PATH / "models"
PIPER_BIN = LIB_PATH / "dist" / "piper"

class Voice:
    def __init__(
            self, 
            voice_model_name="en_US-danny-low.onnx",
            voice_sample_rate=16000,
            on_speak: Optional[Callable[[bool], None]] = None,
        ):
        self._model_path = MODELS_PATH / f"{voice_model_name}.onnx"
        self._sample_rate = voice_sample_rate
        self._speech_lock = threading.Lock()
        self._proc = None
        self._aplay = None

        # Callback handlers
        self.__on_speak = on_speak
        
        if not PIPER_BIN.exists():
            print(f"[Voice Warning]: Piper binary not found at {PIPER_BIN}")
            return

        os.chmod(PIPER_BIN, 0o755)
        
        # Register cleanup to kill processes on exit
        atexit.register(self.stop)
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def _start_engine(self):
        """Start a Piper process and an aplay consumer for one utterance."""
        try:
            self._proc = subprocess.Popen(
                [str(PIPER_BIN), "--model", str(self._model_path), "--output_raw"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                bufsize=0
            )
            
            self._aplay = subprocess.Popen(
                ["aplay", "-r", str(self._sample_rate), "-f", "S16_LE", "-t", "raw"],
                stdin=self._proc.stdout,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                bufsize=0
            )
            self._proc.stdout.close()
        except Exception as e:
            print(f"[Voice Error]: Failed to start TTS engine: {e}")
            self._proc = None
            self._aplay = None

    def say(self, text):
        """Synthesize and play one utterance without overlapping speech."""
        def task():
            with self._speech_lock:
                try:
                    if self.__on_speak:
                        self.__on_speak(True)

                    self._start_engine()
                    if not self._proc or not self._aplay:
                        raise RuntimeError("TTS pipeline did not start")

                    self._proc.communicate(input=f"{text.strip()}\n".encode("utf-8"))
                    self._aplay.wait()
                except Exception as e:
                    print(f"[Voice Error]: {e}")
                finally:
                    if self.__on_speak:
                        self.__on_speak(False)
                    self._proc = None
                    self._aplay = None

        threading.Thread(target=task, daemon=True).start()

    def _handle_signal(self, signum, frame):
        self.stop()
        exit(0)

    def stop(self):
        """Clean shutdown of subprocesses."""
        print("[Voice]: Shutting down TTS engine...")
        if self._proc:
            self._proc.terminate()
            self._proc.wait(timeout=2)
        if self._aplay:
            self._aplay.terminate()
            self._aplay.wait(timeout=2)