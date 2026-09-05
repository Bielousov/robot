import atexit
import subprocess
import time
from pathlib import Path
from typing import Callable, Optional

import numpy as np

# Use the existing Process architecture
from .Threads import Threads

LIB_PATH = Path(__file__).parent.resolve()
HAILO_PATH = LIB_PATH / "hailo"
MODELS_PATH = HAILO_PATH / "models"

def rms_dbfs(data: bytes) -> float:
    """RMS level of 16-bit PCM audio, in dBFS (0 dBFS = full scale)."""
    samples = np.frombuffer(data, dtype=np.int16).astype(np.float32)
    if samples.size == 0:
        return -float("inf")
    rms = np.sqrt(np.mean(np.square(samples)))
    if rms <= 0:
        return -float("inf")
    return 20 * np.log10(rms / 32768.0)


class Ears:
    def __init__(
            self,
            wake_word: str,
            model_name: str,
            sample_rate: int = 16000,
            wake_aliases = '',
            on_listen: Optional[Callable[[str], bool]] = None,
            on_record: Optional[Callable[[str], bool]] = None,
            on_wake: Optional[Callable[[str], None]] = None,
            debug: bool = False,
            noise_gate_dbfs: float = -45.0,
            min_speech_ms: float = 500,
        ):

        self._debug = debug

        # Paths
        model_full_path = MODELS_PATH / model_name
        if not model_full_path.exists():
            raise FileNotFoundError(f"Hailo Whisper model not found at {model_full_path}")

        # Hailo Whisper Setup
        from hailo_platform.genai import Speech2Text, Speech2TextTask

        from .hailo.device import get_vdevice

        self._task = Speech2TextTask.TRANSCRIBE
        self._vdevice = get_vdevice()
        print(f"[Ears] Loading Whisper model '{model_full_path.name}'...")
        self._s2t = Speech2Text(self._vdevice, str(model_full_path))
        print(f"[Ears] Whisper model '{model_full_path.name}' is ready.")

        # Audio Config
        self.sample_rate = sample_rate
        self.wake_word = wake_word.lower()
        self.wake_aliases = [word.strip().lower() for word in wake_aliases.split(',')]

        # Keep chunks short enough for responsive capture without excessive
        # per-call overhead on the Pi.
        self.sample_length_ms = 160
        self.buffer_size = int((self.sample_rate / 1000) * self.sample_length_ms * 2)
        self.silence_timeout_ms = 300
        self.silence_bytes = 0

        # Noise gate: a plain RMS/dBFS threshold. Whisper's acoustic model
        # is sensitive enough that quiet hums/electrical noise get
        # transcribed as hallucinated text rather than rejected outright,
        # so a level-based gate is needed to keep it from being fed
        # anything at all below the threshold. min_speech_ms additionally
        # drops utterances that are mostly silence tail with only a noise
        # blip of real gated-open audio, since Whisper hallucinates filler
        # words ("So,", "You", "The") on slivers of near-silence.
        self.noise_gate_dbfs = noise_gate_dbfs
        self.min_speech_bytes = int(self.sample_rate * 2 * min_speech_ms / 1000)
        self.max_utterance_ms = 15_000

        # Threading Management
        self.__threads = Threads()
        self.__process_handle = None # Subprocess for arecord
        self.__speech_active = False
        self.__speech_bytes = 0
        self.__utterance_frames = []
        self.__utterance_start = 0.0

        # Callback handlers
        self.__on_listen = on_listen
        self.__on_record = on_record
        self.__on_wake = on_wake

        # Cleanup on exit
        atexit.register(self.stop_listening)

    def _cleanup(self, text: str) -> str:
        text = text.lower().strip()
        wake_aliases = self.wake_aliases
        for alias in wake_aliases:
            text = text.replace(alias, self.wake_word)

        words_to_remove = ["huh"]
        for word in words_to_remove:
            text = text.replace(word, "").strip()

        # Filter out very short utterances (noise/false positives)
        has_wake_word = self.wake_word in text

        # Only keep if: contains wake word OR has 2+ words
        # Reject all single short words (articles, prepositions, etc.)
        if not (has_wake_word or len(text) >= 5):
            return ""  # Filter out noise like single "the", "a", "is", etc.

        return text

    def _validate(self, text: str) -> bool:
        return self.wake_word in text

    def _capture_audio(self):
        """The core loop called by the Threads manager."""
        # Ensure the subprocess is alive
        if not self.__process_handle or self.__process_handle.poll() is not None:
            self.__process_handle = subprocess.Popen(
                ["arecord", "-D", "plughw:0,0", "-f", "S16_LE", "-r", str(self.sample_rate), "-c", "1", "-t", "raw"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=self.buffer_size
            )

        # Read audio - blocking, waits for data to arrive
        data = self.__process_handle.stdout.read(self.buffer_size)

        # Check for arecord errors
        if self.__process_handle.poll() is not None:
            # Subprocess exited, check stderr
            try:
                stderr = self.__process_handle.stderr.read().decode('utf-8', errors='ignore')
                if stderr:
                    print(f"[Ears] arecord error: {stderr}")
            except:
                pass

        if not data:
            return

        # Noise gate: only treat this chunk as speech if it's loud enough.
        level = rms_dbfs(data)
        has_speech = level >= self.noise_gate_dbfs

        if has_speech:
            if not self.__speech_active:
                self.__utterance_start = time.time()
                self.__speech_bytes = 0
            self.__speech_active = True
            self.silence_bytes = 0
            self.__speech_bytes += len(data)
            self.__utterance_frames.append(data)
            if self.__on_listen:
                self.__on_listen(True)
            return

        if not self.__speech_active:
            return

        # Keep feeding a short silence tail so the utterance can be finalized.
        self.silence_bytes += len(data)
        self.__utterance_frames.append(data)

        elapsed_ms = (time.time() - self.__utterance_start) * 1000
        silence_timeout = self.silence_bytes >= (
            self.sample_rate * 2 * self.silence_timeout_ms / 1000
        )
        if not (silence_timeout or elapsed_ms >= self.max_utterance_ms):
            return

        pcm_bytes = b"".join(self.__utterance_frames)
        speech_bytes = self.__speech_bytes

        self.__speech_active = False
        self.silence_bytes = 0
        self.__speech_bytes = 0
        self.__utterance_frames = []

        if speech_bytes < self.min_speech_bytes:
            if self._debug:
                dropped_ms = speech_bytes / (self.sample_rate * 2) * 1000
                print(f"[Ears] Dropped short utterance ({dropped_ms:.0f}ms speech)")
            return

        # Process with Whisper
        start_time = time.time()
        try:
            audio = np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float32) / 32768.0
            text = self._s2t.generate_all_text(audio_data=audio, task=self._task, language="en").strip()
        except Exception as e:
            print(f"[Ears] Whisper transcribe error: {e}")
            return
        process_time = time.time() - start_time
        if self._debug:
            print(f"[Ears] Processing time: {process_time*1000:.2f}ms")

        text = self._cleanup(text)

        if text:
            # Print transcript of heard speech
            if self._debug:
                print(f"[Ears] Heard: {text}")

            # Call on_record callback for ALL detected speech and check gate
            gate_check = True  # Default to allow processing
            if self.__on_record:
                gate_check = self.__on_record(text)

            # If gate returned False, stop processing further
            if gate_check is False:
                return

            # Call on_wake callback ONLY if wake word is detected
            if self._validate(text):
                self._on_wake_word_detected(text)


    def _on_wake_word_detected(self, text):
        """Internal handler that triggers the external callback."""
        # Trigger the callback passed from main.py if it exists
        if self.__on_wake:
            self.__on_wake(text)

    def start_listening(self):
        """Initializes the background thread loop."""
        # interval=0 ensures the loop runs as fast as the audio stream provides data
        self.__threads.start(interval=0, function=self._capture_audio)
        print(f"[Ears]: Started listening for '{self.wake_word}'...")

    def stop_listening(self):
        """Stops threads and kills arecord.

        Deliberately not releasing self._s2t/self._vdevice here: the
        vdevice is the shared HailoRT device (lib/hailo/device.py) also
        used by Mind's HailoClient, so this must not tear it down - and
        explicitly releasing HailoRT resources during process shutdown is
        known to throw (see Mind.stop()'s comment for the same reasoning).
        Leaving cleanup to the interpreter during shutdown is silent and
        clean.
        """
        self.__threads.stop()
        if self.__process_handle:
            self.__process_handle.terminate()
            self.__process_handle.wait()
            self.__process_handle = None

        print("[Ears]: Stopped.")
