import atexit
import subprocess
import time
from pathlib import Path
from typing import Callable, Optional

# Use the existing Process architecture
from .Threads import Threads
from .hailo.whisper import UtteranceSegmenter, WhisperClient

LIB_PATH = Path(__file__).parent.resolve()
HAILO_PATH = LIB_PATH / "hailo"
MODELS_PATH = HAILO_PATH / "models"


class Ears:
    def __init__(
            self,
            wake_word: str,
            model_name: str,
            sample_rate: int = 16000,
            wake_aliases = '',
            on_listen: Optional[Callable[[bool], None]] = None,
            on_record: Optional[Callable[[str], bool]] = None,
            on_wake: Optional[Callable[[str], None]] = None,
            debug: bool = False,
        ):

        self._debug = debug

        # Hailo Whisper setup. WhisperClient shares the process-wide VDevice
        # (lib/hailo/device.py) itself and also adds repetition-penalty,
        # spectral-ratio and crest-factor hallucination/noise filtering this
        # class didn't previously have - see lib/hailo/whisper.py.
        print(f"[Ears] Loading Whisper model '{model_name}'...")
        self._engine = WhisperClient(model_name, sample_rate=sample_rate)
        print(f"[Ears] Whisper model '{model_name}' is ready.")

        # Audio Config
        self.sample_rate = sample_rate
        self.wake_word = wake_word.lower()
        self.wake_aliases = [word.strip().lower() for word in wake_aliases.split(',')]

        # Keep chunks short enough for responsive capture without excessive
        # per-call overhead on the Pi.
        self.sample_length_ms = 160
        self.buffer_size = int((self.sample_rate / 1000) * self.sample_length_ms * 2)

        # Segmentation via Silero VAD (see lib/hailo/whisper.py). No
        # early/pause-based emission here - wake-word utterances are short
        # and should be transcribed whole, not split mid-phrase the way the
        # console test harness splits long conversational speech.
        self._segmenter = UtteranceSegmenter(
            sample_rate,
            silence_timeout_ms=300,
            max_utterance_ms=15_000,
            min_speech_ms=100,
            early_transcribe_ms=0,
            on_vad_change=self._on_vad_change,
        )

        # Threading Management
        self.__threads = Threads()
        self.__process_handle = None # Subprocess for arecord

        # Callback handlers
        self.__on_listen = on_listen
        self.__on_record = on_record
        self.__on_wake = on_wake

        # Cleanup on exit
        atexit.register(self.stop_listening)

    def _on_vad_change(self, is_speech: bool):
        """Forwards Silero VAD speech/silence transitions to on_listen."""
        if self.__on_listen:
            self.__on_listen(is_speech)

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

        utterance = self._segmenter.process(data)
        if not utterance:
            return

        pcm_bytes, utterance_ms = utterance

        # Process with Whisper - repetition penalty, spectral/crest-factor
        # filtering, auto-gain and dedup all happen inside transcribe().
        start_time = time.time()
        try:
            text = self._engine.transcribe(pcm_bytes)
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

        Deliberately not calling self._engine.stop() here: that would
        release the Speech2Text handle, and explicitly releasing HailoRT
        resources during process shutdown is known to throw (see
        Mind.stop()'s comment for the same reasoning). This method runs in
        that same process-exit path (main.py's shutdown sequence, and as an
        atexit safety net), so leaving cleanup to the interpreter during
        shutdown is silent and clean.
        """
        self.__threads.stop()
        if self.__process_handle:
            self.__process_handle.terminate()
            self.__process_handle.wait()
            self.__process_handle = None

        print("[Ears]: Stopped.")
