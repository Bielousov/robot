import json
import subprocess
import os
import threading
import atexit
from collections import deque
from pathlib import Path
from vosk import Model, KaldiRecognizer, SetLogLevel

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
            stack_size: int = 4,
            wake_word_synonyms = '',
            debug: bool = False,
            on_record = None,
            on_wake = None,
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
        self.stack = deque(maxlen=stack_size)
        self.wake_word = wake_word.lower()
        self.wake_word_synonyms = [word.strip().lower() for word in wake_word_synonyms.split(',')]

        print (f"SYNONYMS: {self.wake_word_synonyms}")
        
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
        wake_word_synonyms = self.wake_word_synonyms
        for synonym in wake_word_synonyms:
            text = text.replace(synonym, self.wake_word)

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
                ["arecord", "-f", "S16_LE", "-r", str(self.sample_rate), "-c", "1", "-t", "raw", "-q"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                bufsize=0
            )

        # Read a chunk of audio
        data = self.__process_handle.stdout.read(4000)

        if self.__on_record and not self.__on_record():
            self.recognizer.Reset()
            return
        
        if not data:
            return

        # Process with Vosk
        if self.recognizer.AcceptWaveform(data):
            result = json.loads(self.recognizer.Result())
            text = self._cleanup(result.get("text", ""))
            
            if text:
                self.stack.append(text)
                if self.debug:
                    print(f"Captured Speech: {text}")
                if self._validate(text):
                    self._on_wake_word_detected(text, list(self.stack))
                    self.stack.clear()
        else:
            # You can handle partial results here if needed
            # partial = json.loads(self.recognizer.PartialResult())
            pass


    def _on_wake_word_detected(self, text, conversation_history):
        """Internal handler that triggers the external callback."""
        if self.debug:
            print(f"Wake word detected: '{text}' {conversation_history}")
        
        # 3. Trigger the callback passed from main.py if it exists
        if self.__on_wake:
            self.__on_wake(text, conversation_history)

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
