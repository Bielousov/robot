import json
import subprocess
import atexit
from pathlib import Path
from typing import Callable, Optional
from vosk import Model, KaldiRecognizer, SetLogLevel
import webrtcvad
import time

# Use the existing Process architecture
from .Threads import Threads

LIB_PATH = Path(__file__).parent.resolve()
VOSK_PATH = LIB_PATH / "vosk"
MODELS_PATH = VOSK_PATH / "models"

class Ears:
    def __init__(
            self,
            wake_word: str,
            model_name: str,
            sample_rate: int = 16000,
            wake_aliases = '',
            debug: bool = False,
            on_listen: Optional[Callable[[str], bool]] = None,
            on_record: Optional[Callable[[str], bool]] = None,
            on_wake: Optional[Callable[[str], None]] = None,
        ):
    
        self.debug = debug;
        SetLogLevel(0 if self.debug else -1)

        # Paths
        model_full_path = MODELS_PATH / model_name
        if not model_full_path.exists():
            raise FileNotFoundError(f"Vosk model not found at {model_full_path}")

        # Vosk Setup
        self.model = Model(str(model_full_path))
        self.recognizer = KaldiRecognizer(self.model, sample_rate)
        
        # Audio Config
        self.sample_rate = sample_rate
        self.wake_word = wake_word.lower()
        self.wake_aliases = [word.strip().lower() for word in wake_aliases.split(',')]
        
        # Audio chunk size: 250ms for Vosk processing
        self.sample_length_ms = 250
        self.buffer_size = int((self.sample_rate / 1000) * self.sample_length_ms * 2)

        # VAD Setup
        self.vad = webrtcvad.Vad(2)
        # VAD frame size: 20ms * 2 bytes per sample (16-bit)
        self.vad_frame_size = int((self.sample_rate / 1000) * 20 * 2)

        
        # Threading Management
        self.__threads = Threads()
        self.__process_handle = None # Subprocess for arecord

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
        # Keep only if: contains wake word OR has 2+ words OR is 3+ characters
        words = text.split()
        has_wake_word = self.wake_word in text
        is_substantial = len(words) >= 2 or len(text) >= 3
        
        if not (has_wake_word or is_substantial):
            return ""  # Filter out noise like single "the", "a", etc.

        return text
    
    def _validate(self, text: str) -> bool:
        return self.wake_word in text

    def _capture_audio(self):
        """The core loop called by the Threads manager."""
        # Ensure the subprocess is alive
        if not self.__process_handle or self.__process_handle.poll() is not None:
            self.__process_handle = subprocess.Popen(
                ["arecord", "-f", "S16_LE", "-r", str(self.sample_rate), "-c", "1", "-t", "raw"],
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

        # Check if audio has voice activity before processing with Vosk
        # VAD requires 10ms, 20ms, or 30ms frames
        # At 16kHz: 20ms = 320 samples * 2 bytes (16-bit) = 640 bytes
        
        has_speech = False
        try:
            # Process audio in 20ms chunks through VAD
            for i in range(0, len(data), self.vad_frame_size):
                frame = data[i:i+self.vad_frame_size]
                if len(frame) == self.vad_frame_size:  # Only process complete frames
                    if self.vad.is_speech(frame, self.sample_rate):
                        has_speech = True
                        if self.__on_listen:
                            self.__on_listen(True)
                        break
        except Exception as e:
            has_speech = True  # Default to True if VAD fails
            if self.debug:
                print(f"[VAD] Error: {e}")

        # Skip Vosk processing if no speech detected
        if not has_speech:
            return

        # Process with Vosk
        start_time = time.time()
        if self.recognizer.AcceptWaveform(data):
            process_time = time.time() - start_time
            if self.debug:
                print(f"[Vosk] Processing time: {process_time*1000:.2f}ms")
            
            result = json.loads(self.recognizer.Result())
            text = self._cleanup(result.get("text", ""))
            
            if text:
                # Print transcript of heard speech
                print(f"[Ears] Heard: {text}")
                
                # Call on_record callback for ALL detected speech and check gate
                gate_check = True  # Default to allow processing
                if self.__on_record:
                    gate_check = self.__on_record(text)
                
                # If gate returned False, stop processing further
                if gate_check is False:
                    self.recognizer.Reset()
                    return
                
                # Call on_wake callback ONLY if wake word is detected
                if self._validate(text):
                    self._on_wake_word_detected(text)
        else:
            # You can handle partial results here if needed
            # partial = json.loads(self.recognizer.PartialResult())
            pass


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
        """Stops threads and kills arecord."""
        self.__threads.stop()
        if self.__process_handle:
            self.__process_handle.terminate()
            self.__process_handle.wait()
            self.__process_handle = None
        
        print("[Ears]: Stopped.")
