import os
import queue
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


class _Utterance:
    """One queued utterance. Synthesized audio is buffered here until it's
    this utterance's turn to play."""

    def __init__(self, text: str):
        self.text = text
        self.audio: Optional[bytes] = None
        self.error: Optional[Exception] = None
        self.ready = threading.Event()


class Voice:
    def __init__(
            self,
            voice_model_name="en_US-danny-low.onnx",
            voice_sample_rate=16000,
            on_speak: Optional[Callable[[bool], None]] = None,
        ):
        self._model_path = MODELS_PATH / f"{voice_model_name}.onnx"
        self._sample_rate = voice_sample_rate
        self._playback_lock = threading.Lock()
        self._aplay = None

        # Utterances are queued here in call order; a single worker thread
        # plays them out strictly one at a time, in that order, while
        # synthesis for later utterances can run concurrently in the background.
        self._playback_queue = queue.Queue()
        self._playback_thread = threading.Thread(target=self._playback_worker, daemon=True)
        self._playback_thread.start()

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

    def say(self, text):
        """Queue one utterance for speech.

        Synthesis starts right away in the background; playback is handled by
        the dedicated worker thread, strictly in the order utterances were
        queued, one at a time.
        """
        utterance = _Utterance(text)
        self._playback_queue.put(utterance)
        threading.Thread(target=self._synthesize, args=(utterance,), daemon=True).start()

    def _synthesize(self, utterance: "_Utterance"):
        """Run Piper for one utterance and buffer its raw PCM output.

        is_speaking brackets this synthesis step (not playback), so the next
        utterance can start synthesizing as soon as this one is done, even
        while its audio is still queued or playing.
        """
        if self.__on_speak:
            self.__on_speak(True)

        try:
            proc = subprocess.Popen(
                [str(PIPER_BIN), "--model", str(self._model_path), "--output_raw"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )
            audio, _ = proc.communicate(input=f"{utterance.text.strip()}\n".encode("utf-8"))
            utterance.audio = audio
        except Exception as e:
            utterance.error = e
        finally:
            if self.__on_speak:
                self.__on_speak(False)
            utterance.ready.set()

    def _playback_worker(self):
        """Plays queued utterances strictly in order, one at a time.

        Each utterance's synthesized audio is buffered (via `ready`/`audio`)
        until playback of every earlier-queued utterance has finished.
        """
        while True:
            utterance = self._playback_queue.get()
            if utterance is None:
                break

            utterance.ready.wait()

            if utterance.error:
                print(f"[Voice Error]: {utterance.error}")
                continue
            if not utterance.audio:
                continue

            with self._playback_lock:
                try:
                    self._aplay = subprocess.Popen(
                        ["aplay", "-r", str(self._sample_rate), "-f", "S16_LE", "-t", "raw"],
                        stdin=subprocess.PIPE,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    self._aplay.communicate(input=utterance.audio)
                except Exception as e:
                    print(f"[Voice Error]: {e}")
                finally:
                    self._aplay = None

    def _handle_signal(self, signum, frame):
        self.stop()
        exit(0)

    def stop(self):
        """Clean shutdown of subprocesses."""
        print("[Voice]: Shutting down TTS engine...")
        if self._aplay:
            self._aplay.terminate()
            try:
                self._aplay.wait(timeout=2)
            except subprocess.TimeoutExpired:
                pass
        self._playback_queue.put(None)
