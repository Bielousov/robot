import os
import subprocess
import threading
import atexit
import signal
from pathlib import Path

# Paths (Assuming same structure)
LIB_PATH = Path(__file__).parent.resolve() / "piper"
MODELS_PATH = LIB_PATH / "models"
PIPER_BIN = LIB_PATH / "dist" / "piper"

class Voice:
    def __init__(self, voice_model_name="en_US-danny-low.onnx", voice_sample_rate=16000):
        self._model_path = MODELS_PATH / f"{voice_model_name}.onnx"
        self._sample_rate = voice_sample_rate
        self._speech_lock = threading.Lock()
        
        # Persistent process handle
        self._proc = None
        self._aplay = None
        
        if not PIPER_BIN.exists():
            print(f"[Voice Warning]: Piper binary not found at {PIPER_BIN}")
            return

        os.chmod(PIPER_BIN, 0o755)
        self._start_engine()
        
        # Register cleanup to kill processes on exit
        atexit.register(self.stop)
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def _start_engine(self):
        """Starts Piper and aplay in a persistent pipeline."""
        try:
            # We start Piper in 'raw' mode, outputting to stdout
            self._proc = subprocess.Popen(
                [str(PIPER_BIN), "--model", str(self._model_path), "--output_raw"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                bufsize=0
            )
            
            # We pipe Piper's stdout directly into aplay
            self._aplay = subprocess.Popen(
                ["aplay", "-r", str(self._sample_rate), "-f", "S16_LE", "-t", "raw"],
                stdin=self._proc.stdout,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                bufsize=0
            )
        except Exception as e:
            print(f"[Voice Error]: Failed to start TTS engine: {e}")

    def say(self, text, callback=None):
        """Sends text to Piper and executes callback after audio finishes playing."""
        def task():
            with self._speech_lock:
                try:
                    if not self._proc or self._proc.poll() is not None:
                        self._start_engine()
                    
                    # Send text to Piper
                    input_text = f"{text.strip()}\n"
                    self._proc.stdin.write(input_text.encode("utf-8"))
                    self._proc.stdin.flush()

                    # Launch a temporary aplay to play Piper's current stdout
                    # Use a pipe to read Piper's output until it's done
                    piper_output = self._proc.stdout.read()  # blocks until audio ready
                    if not piper_output:
                        raise RuntimeError("No audio produced by Piper.")

                    # Play the captured audio and wait for it to finish
                    aplay_proc = subprocess.Popen(
                        ["aplay", "-r", str(self._sample_rate), "-f", "S16_LE", "-t", "raw"],
                        stdin=subprocess.PIPE,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    aplay_proc.communicate(input=piper_output)  # blocks until playback ends

                    # Audio finished, call callback
                    if callback:
                        callback(success=True)

                except Exception as e:
                    print(f"[Voice Error]: {e}")
                    if callback:
                        callback(success=False, error=str(e))

        threading.Thread(target=task, daemon=True).start()


    def _handle_signal(self, signum, frame):
        self.stop()
        exit(0)

    def stop(self):
        """Clean shutdown of subprocesses."""
        print("[Voice]: Shutting down TTS engine...")
        if self._proc:
            self._proc.terminate()
            self._proc.wait()
        if self._aplay:
            self._aplay.terminate()
            self._aplay.wait()