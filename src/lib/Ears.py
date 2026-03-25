import json
import subprocess
import atexit
import warnings
from pathlib import Path
from vosk import Model, KaldiRecognizer, SetLogLevel

# Suppress deprecated pkg_resources warning from webrtcvad
warnings.filterwarnings("ignore", category=UserWarning, message=".*pkg_resources.*")
import webrtcvad

# Use the existing Process architecture
from .Threads import Process, Threads

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
            on_record = None,
            on_wake = None,
            vad_aggressiveness: int = 0, # 0=most sensitive for faint mics, 3=aggressive
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
        
        # VAD Setup (WebRTC Voice Activity Detection)
        # Aggressiveness: 0-3 (higher = more aggressive filtering)
        # With faint mics, use 0 (most sensitive)
        self.vad = webrtcvad.Vad(vad_aggressiveness)
        
        # Audio Config
        self.sample_rate = sample_rate
        self.wake_word = wake_word.lower()
        self.wake_aliases = [word.strip().lower() for word in wake_aliases.split(',')]
        
        # VAD stats for debugging
        self.__vad_frames_total = 0
        self.__vad_frames_speech = 0

        print (f"SYNONYMS: {self.wake_aliases}")
        print (f"VAD Aggressiveness: {vad_aggressiveness} (0=sensitive, 3=aggressive)")
        
        # Threading Management
        self.__threads = Threads()
        self.__process_handle = None # Subprocess for arecord

        # Callback handlers
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

        return text
    
    def _validate(self, text: str) -> bool:
        return self.wake_word in text

    def _capture_audio(self):
        """The core loop called by the Threads manager."""
        # Ensure the subprocess is alive
        if not self.__process_handle or self.__process_handle.poll() is not None:
            self.__process_handle = subprocess.Popen(
                ["arecord", "-D", "default", "-f", "S16_LE", "-r", str(self.sample_rate), "-c", "1", "-t", "raw", "-q"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE if self.debug else subprocess.DEVNULL,
                bufsize=0
            )

        # Read a chunk of audio
        data = self.__process_handle.stdout.read(4000)

        if self.__on_record and not self.__on_record():
            self.recognizer.Reset()
            return
        
        if not data:
            return

        # VAD pre-filtering: Skip silent frames before Vosk processing
        # This significantly reduces CPU load by avoiding unnecessary Vosk processing
        self.__vad_frames_total += 1
        try:
            is_speech = self.vad.is_speech(data, self.sample_rate)
        except Exception as e:
            if self.debug:
                print(f"VAD error: {e}")
            is_speech = True  # Process on VAD errors to be safe
        
        if not is_speech:
            # Silence detected, skip Vosk processing
            self.recognizer.Reset()
            return
        
        # Speech detected, update statistics
        self.__vad_frames_speech += 1

        # Process with Vosk only if speech was detected
        if self.recognizer.AcceptWaveform(data):
            result = json.loads(self.recognizer.Result())
            text = self._cleanup(result.get("text", ""))
            
            if text:
                # Notify caller of recognized text for state management
                if self.__on_record:
                    self.__on_record(text)
                
                if self.debug:
                    print(f"Captured Speech: {text}")
                if self._validate(text):
                    self._on_wake_word_detected(text)
        else:
            # You can handle partial results here if needed
            # partial = json.loads(self.recognizer.PartialResult())
            pass


    def _on_wake_word_detected(self, text):
        """Internal handler that triggers the external callback."""
        if self.debug:
            print(f"Wake word detected: '{text}'")
        
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
        
        # Print VAD statistics if available
        if self.__vad_frames_total > 0:
            speech_ratio = (self.__vad_frames_speech / self.__vad_frames_total) * 100
            print(f"[Ears]: Stopped. VAD Statistics - Processed {self.__vad_frames_speech}/{self.__vad_frames_total} frames ({speech_ratio:.1f}% speech)")
        else:
            print("[Ears]: Stopped.")
