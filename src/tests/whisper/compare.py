"""
Side-by-side speech-to-text comparison: Vosk (CPU) vs Whisper (HailoRT).

Listens to the mic continuously and runs two independent utterance
segmenters over the same audio stream:
    - Vosk is fed utterances gated by WebRTC VAD (same approach as
      lib/Ears.py) - a speech/non-speech classifier.
    - Whisper is fed utterances gated by a simple RMS noise gate instead.
      Whisper's acoustic model is sensitive enough that VAD-passed hums,
      electrical noise and near-silence get transcribed as hallucinated
      text ("the", "going to be...") rather than rejected outright, so it
      needs a level-based gate rather than a speech classifier.

Each engine's transcript plus timing (utterance length, inference latency)
is printed to the console so the two can be compared for accuracy and speed.

Usage:
    python src/tests/whisper/compare.py

Env vars (all optional, see src/config.py for the same names used elsewhere):
    VOSK_MODEL_NAME           Vosk model dir name under lib/vosk/models (required)
    HAILO_WHISPER_MODEL_HEF   Whisper HEF file name under lib/hailo/models (required
                              for the Hailo side; e.g. "whisper-tiny.hef")
    VOSK_SAMPLE_RATE          Mic/recognizer sample rate, default 16000
    MIC_DEVICE                arecord -D device string, e.g. "plughw:0,0"
    WHISPER_NOISE_GATE_DBFS   RMS noise gate threshold for Whisper, default -40.0
"""

import json
import queue
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import webrtcvad
from vosk import Model, KaldiRecognizer, SetLogLevel

# Anchor to project root (src) so `config` and `lib` resolve like other tests.
PROJECT_PATH = Path(__file__).parent.parent.parent.resolve()
if str(PROJECT_PATH) not in sys.path:
    sys.path.insert(0, str(PROJECT_PATH))

from config import Env

VOSK_MODELS_PATH = PROJECT_PATH / "lib" / "vosk" / "models"
HAILO_MODELS_PATH = PROJECT_PATH / "lib" / "hailo" / "models"

SAMPLE_RATE = Env.VoskSampleRate
MIC_DEVICE = os.getenv("MIC_DEVICE")

# Utterance segmentation (mirrors lib/Ears.py)
VAD_FRAME_MS = 20
VAD_FRAME_BYTES = int((SAMPLE_RATE / 1000) * VAD_FRAME_MS * 2)
READ_CHUNK_BYTES = VAD_FRAME_BYTES * 4
SILENCE_TIMEOUT_MS = 500
MAX_UTTERANCE_MS = 15_000

# Whisper noise gate: a plain RMS/dBFS threshold instead of a speech
# classifier, since VAD happily passes hums/electrical noise that Whisper
# then hallucinates text for. -55 dBFS is a starting point for mic setups
# with no hardware/AGC gain; watch the "[Whisper Gate]" transitions printed
# at runtime and raise/lower WHISPER_NOISE_GATE_DBFS to match your input
# level (louder threshold = fewer false triggers, but risks gating out
# quiet real speech - as happened at the previous -40 default).
NOISE_GATE_DBFS = float(os.getenv("WHISPER_NOISE_GATE_DBFS", "-55.0"))


def rms_dbfs(data: bytes) -> float:
    """RMS level of 16-bit PCM audio, in dBFS (0 dBFS = full scale)."""
    samples = np.frombuffer(data, dtype=np.int16).astype(np.float32)
    if samples.size == 0:
        return -float("inf")
    rms = np.sqrt(np.mean(np.square(samples)))
    if rms <= 0:
        return -float("inf")
    return 20 * np.log10(rms / 32768.0)


class UtteranceSegmenter:
    """Turns a stream of raw PCM chunks into finished utterances.

    `is_speech_fn(chunk) -> bool` decides whether a given chunk counts as
    speech; everything else about buffering, the silence hangover and the
    max-length cutoff is shared, so Vosk (VAD-gated) and Whisper
    (noise-gated) can each run their own instance over the same audio.
    """

    def __init__(self, is_speech_fn, sample_rate: int, silence_timeout_ms: int, max_utterance_ms: int):
        self._is_speech_fn = is_speech_fn
        self._sample_rate = sample_rate
        self._silence_timeout_bytes = int(sample_rate * 2 * silence_timeout_ms / 1000)
        self._max_utterance_ms = max_utterance_ms

        self._speech_active = False
        self._silence_bytes = 0
        self._frames = []
        self._start_time = 0.0

    def process(self, data: bytes):
        """Feed one chunk of audio. Returns (pcm_bytes, utterance_ms) when
        an utterance just finished, otherwise None."""
        has_speech = self._is_speech_fn(data)

        if has_speech:
            if not self._speech_active:
                self._start_time = time.time()
            self._speech_active = True
            self._silence_bytes = 0
            self._frames.append(data)
            return None

        if not self._speech_active:
            return None

        self._silence_bytes += len(data)
        self._frames.append(data)

        elapsed_ms = (time.time() - self._start_time) * 1000
        silence_timeout = self._silence_bytes >= self._silence_timeout_bytes
        if not (silence_timeout or elapsed_ms >= self._max_utterance_ms):
            return None

        pcm_bytes = b"".join(self._frames)
        utterance_ms = (time.time() - self._start_time) * 1000

        self._speech_active = False
        self._silence_bytes = 0
        self._frames = []
        return pcm_bytes, utterance_ms


class VoskEngine:
    """Batch-mode wrapper so timing is comparable to the Hailo side."""

    def __init__(self, model_name: str, sample_rate: int):
        model_path = VOSK_MODELS_PATH / model_name
        if not model_path.exists():
            raise FileNotFoundError(f"Vosk model not found at {model_path}")
        SetLogLevel(-1)
        self._model = Model(str(model_path))
        self._sample_rate = sample_rate

    def transcribe(self, pcm_bytes: bytes) -> str:
        rec = KaldiRecognizer(self._model, self._sample_rate)
        rec.AcceptWaveform(pcm_bytes)
        result = json.loads(rec.FinalResult())
        return result.get("text", "").strip()


class HailoWhisperEngine:
    """Wraps hailo_platform.genai.Speech2Text for whisper-on-HailoRT inference."""

    def __init__(self, hef_name: str):
        from hailo_platform import VDevice
        from hailo_platform.genai import Speech2Text, Speech2TextTask

        hef_path = Path(hef_name)
        if not hef_path.is_absolute():
            hef_path = HAILO_MODELS_PATH / hef_name
        if not hef_path.is_file():
            raise FileNotFoundError(f"Hailo Whisper model not found at {hef_path}")

        self._task = Speech2TextTask.TRANSCRIBE
        self._vdevice = VDevice()
        print(f"[Hailo] Loading model '{hef_path.name}'...")
        self._s2t = Speech2Text(self._vdevice, str(hef_path))
        print(f"[Hailo] Model '{hef_path.name}' is ready.")

    def transcribe(self, pcm_bytes: bytes) -> str:
        # Speech2Text expects mono float32 PCM normalized to [-1.0, 1.0) @ 16kHz.
        audio = np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        return self._s2t.generate_all_text(audio_data=audio, task=self._task, language="en").strip()

    def stop(self):
        self._s2t.release()
        self._vdevice.release()


class EngineWorker:
    """Runs one engine's transcribe() on a background thread via a work queue,
    so a slow model never blocks mic capture or the other model."""

    def __init__(self, label: str, engine):
        self.label = label
        self._engine = engine
        self._queue: "queue.Queue[tuple[bytes, float]]" = queue.Queue()
        from lib.Threads import Threads
        self._threads = Threads()
        self._threads.start(interval=0, function=self._run_once)

    def submit(self, pcm_bytes: bytes, utterance_ms: float):
        self._queue.put((pcm_bytes, utterance_ms))

    def _run_once(self):
        try:
            pcm_bytes, utterance_ms = self._queue.get(timeout=0.1)
        except queue.Empty:
            return

        start = time.time()
        try:
            text = self._engine.transcribe(pcm_bytes)
        except Exception as e:
            print(f"[{self.label}] error: {e}")
            return
        latency_ms = (time.time() - start) * 1000

        if text:
            print(f"[{self.label}] utterance={utterance_ms:.0f}ms latency={latency_ms:.0f}ms: {text}")
        else:
            print(f"[{self.label}] utterance={utterance_ms:.0f}ms latency={latency_ms:.0f}ms: (no speech recognized)")

    def stop(self):
        self._threads.stop()
        if hasattr(self._engine, "stop"):
            self._engine.stop()


def start_mic(sample_rate: int, device: str | None) -> subprocess.Popen:
    cmd = ["arecord", "-f", "S16_LE", "-r", str(sample_rate), "-c", "1", "-t", "raw"]
    if device:
        cmd[1:1] = ["-D", device]
    try:
        return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=READ_CHUNK_BYTES)
    except FileNotFoundError:
        print("[ERROR] arecord not found. Install alsa-utils: apt install alsa-utils")
        sys.exit(1)


def main():
    vosk_model_name = Env.VoskModel
    if not vosk_model_name:
        print("[ERROR] VOSK_MODEL_NAME is not set.")
        sys.exit(1)

    vosk_engine = VoskEngine(vosk_model_name, SAMPLE_RATE)
    workers = [EngineWorker("Vosk", vosk_engine)]

    whisper_model_name = os.getenv("HAILO_WHISPER_MODEL_HEF")
    if not whisper_model_name:
        print("[WARN] HAILO_WHISPER_MODEL_HEF is not set - running Vosk only.")
    else:
        try:
            hailo_engine = HailoWhisperEngine(whisper_model_name)
            workers.append(EngineWorker("Whisper/Hailo", hailo_engine))
        except ImportError:
            print("[WARN] hailo_platform not installed on this machine - running Vosk only.")
        except FileNotFoundError as e:
            print(f"[WARN] {e} - running Vosk only.")

    vad = webrtcvad.Vad(2)

    def vad_is_speech(data: bytes) -> bool:
        for i in range(0, len(data), VAD_FRAME_BYTES):
            frame = data[i:i + VAD_FRAME_BYTES]
            if len(frame) == VAD_FRAME_BYTES and vad.is_speech(frame, SAMPLE_RATE):
                return True
        return False

    gate_state = {"open": False}

    def noise_gate_is_speech(data: bytes) -> bool:
        level = rms_dbfs(data)
        is_speech = level >= NOISE_GATE_DBFS
        if is_speech != gate_state["open"]:
            gate_state["open"] = is_speech
            state = "open" if is_speech else "closed"
            print(f"[Whisper Gate] {state} ({level:.1f} dBFS, threshold {NOISE_GATE_DBFS:.1f})")
        return is_speech

    vosk_worker = workers[0]
    whisper_worker = workers[1] if len(workers) > 1 else None

    vosk_segmenter = UtteranceSegmenter(vad_is_speech, SAMPLE_RATE, SILENCE_TIMEOUT_MS, MAX_UTTERANCE_MS)
    whisper_segmenter = UtteranceSegmenter(noise_gate_is_speech, SAMPLE_RATE, SILENCE_TIMEOUT_MS, MAX_UTTERANCE_MS)

    process = start_mic(SAMPLE_RATE, MIC_DEVICE)

    print(f"[Compare] Listening on {SAMPLE_RATE}Hz... (Ctrl+C to stop)")

    try:
        while True:
            data = process.stdout.read(READ_CHUNK_BYTES)
            if not data:
                break

            vosk_utterance = vosk_segmenter.process(data)
            if vosk_utterance:
                vosk_worker.submit(*vosk_utterance)

            if whisper_worker:
                whisper_utterance = whisper_segmenter.process(data)
                if whisper_utterance:
                    whisper_worker.submit(*whisper_utterance)
    except KeyboardInterrupt:
        print("\n[Compare] Stopping...")
    finally:
        for worker in workers:
            worker.stop()
        process.terminate()
        process.wait()


if __name__ == "__main__":
    main()
