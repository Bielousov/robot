import os
import queue
import subprocess
import threading
import time
import atexit
import signal
from pathlib import Path
from typing import Callable, Optional

from lib.Threads import Process

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
            debug: bool = False,
        ):
        self._debug = debug
        self._model_path = MODELS_PATH / f"{voice_model_name}.onnx"
        self._sample_rate = voice_sample_rate
        self._aplay = None

        # Utterances are queued here in call order; a single warm worker
        # plays them out strictly one at a time, in that order, while
        # synthesis for later utterances can run concurrently in the background.
        self._playback_queue = queue.Queue()
        self._playback_process = Process()
        self._playback_process.run(self._playback_worker)

        # Utterances to synthesize are queued here too, and drained by one
        # warm, long-lived worker (via lib.Threads.Process) instead of
        # spinning up a new thread for every chunk.
        self._synthesis_queue = queue.Queue()
        self._synthesis_process = Process()
        self._synthesis_process.run(self._synthesis_worker)

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

        Both queues are fed immediately (never blocking); the warm synthesis
        and playback workers pick utterances up in the order they were queued.
        """
        utterance = _Utterance(text)
        self._playback_queue.put(utterance)
        self._synthesis_queue.put(utterance)

    def _synthesis_worker(self):
        """Warm worker: runs for Voice's whole lifetime, synthesizing queued
        utterances one at a time instead of starting/stopping a thread and a
        Piper process for every chunk.
        """
        while True:
            utterance = self._synthesis_queue.get()
            try:
                if utterance is None:
                    break
                self._synthesize(utterance)
            finally:
                self._synthesis_queue.task_done()

    def _synthesize(self, utterance: "_Utterance"):
        """Run Piper for one utterance and buffer its raw PCM output.

        is_speaking brackets this synthesis step (not playback), so the next
        utterance can start synthesizing as soon as this one is done, even
        while its audio is still queued or playing.
        """
        if self.__on_speak:
            self.__on_speak(True)

        started_at = time.perf_counter()

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
            if self._debug:
                elapsed = time.perf_counter() - started_at
                print(
                    f"[Voice] Synthesized {len(utterance.text)} chars in "
                    f"{elapsed:.3f}s: {utterance.text!r}"
                )

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
            try:
                if utterance is None:
                    break

                utterance.ready.wait()

                if utterance.error:
                    print(f"[Voice Error]: {utterance.error}")
                    continue
                if not utterance.audio:
                    continue

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
            finally:
                self._playback_queue.task_done()

    def wait_until_idle(self, timeout: float = 5.0):
        """Block (up to `timeout` seconds) until every utterance queued so
        far has finished synthesizing and playing.

        Without this, a shutdown right after `say()` (e.g. a goodbye phrase
        followed by Ctrl+C) can kill the daemon worker threads before Piper
        or aplay ever produce sound - the log line prints instantly, but the
        actual synthesis/playback work is still in flight.
        """
        done = threading.Event()

        def _join():
            self._synthesis_queue.join()
            self._playback_queue.join()
            done.set()

        threading.Thread(target=_join, daemon=True).start()
        done.wait(timeout)

    def _handle_signal(self, signum, frame):
        self.wait_until_idle()
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
        self._synthesis_queue.put(None)
        self._playback_queue.put(None)
