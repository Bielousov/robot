"""
Side-by-side speech-to-text comparison: Vosk (CPU) vs Whisper (HailoRT).

Listens to the mic continuously, gates out silence/noise with WebRTC VAD
(same approach as lib/Ears.py), and on every detected utterance runs it
through both engines in parallel background workers. Prints each model's
transcript plus timing (utterance length, inference latency) to the console
so the two can be compared for accuracy and speed.

Usage:
    python src/tests/whisper/compare.py

Env vars (all optional, see src/config.py for the same names used elsewhere):
    VOSK_MODEL_NAME           Vosk model dir name under lib/vosk/models (required)
    HAILO_WHISPER_MODEL_HEF   Whisper HEF file name under lib/hailo/models (required
                              for the Hailo side; e.g. "whisper-tiny.hef")
    VOSK_SAMPLE_RATE          Mic/recognizer sample rate, default 16000
    MIC_DEVICE                arecord -D device string, e.g. "plughw:0,0"
"""

import json
import queue
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

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
MIN_AUDIO_RMS = int(os.getenv("WHISPER_MIN_RMS", "400"))
MIN_VOICED_FRAMES = int(os.getenv("WHISPER_MIN_VOICED_FRAMES", "2"))


def pcm_rms(pcm_bytes: bytes) -> float:
    """Return the RMS amplitude of signed 16-bit mono PCM."""
    samples = np.frombuffer(pcm_bytes, dtype=np.int16)
    if samples.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(samples.astype(np.float32) ** 2)))


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
        if pcm_rms(pcm_bytes) < MIN_AUDIO_RMS:
            return ""
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


def start_mic(sample_rate: int, device: Optional[str]) -> subprocess.Popen:
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
    process = start_mic(SAMPLE_RATE, MIC_DEVICE)

    speech_active = False
    silence_bytes = 0
    utterance_frames = []
    utterance_start = 0.0
    voiced_frames = 0
    voiced_signal_frames = 0

    print(f"[Compare] Listening on {SAMPLE_RATE}Hz... (Ctrl+C to stop)")

    try:
        while True:
            data = process.stdout.read(READ_CHUNK_BYTES)
            if not data:
                break

            has_speech = False
            chunk_voiced_frames = 0
            chunk_voiced_signal_frames = 0
            for i in range(0, len(data), VAD_FRAME_BYTES):
                frame = data[i:i + VAD_FRAME_BYTES]
                if len(frame) != VAD_FRAME_BYTES:
                    continue
                if vad.is_speech(frame, SAMPLE_RATE):
                    chunk_voiced_frames += 1
                    if pcm_rms(frame) >= MIN_AUDIO_RMS:
                        chunk_voiced_signal_frames += 1

            has_speech = chunk_voiced_signal_frames > 0

            if has_speech:
                if not speech_active:
                    utterance_start = time.time()
                    voiced_frames = 0
                    voiced_signal_frames = 0
                speech_active = True
                silence_bytes = 0
                voiced_frames += chunk_voiced_frames
                voiced_signal_frames += chunk_voiced_signal_frames
                utterance_frames.append(data)
            elif speech_active:
                silence_bytes += len(data)
                utterance_frames.append(data)

                elapsed_ms = (time.time() - utterance_start) * 1000
                silence_timeout = silence_bytes >= (SAMPLE_RATE * 2 * SILENCE_TIMEOUT_MS / 1000)
                if silence_timeout or elapsed_ms >= MAX_UTTERANCE_MS:
                    pcm_bytes = b"".join(utterance_frames)
                    utterance_ms = (time.time() - utterance_start) * 1000
                    utterance_rms = pcm_rms(pcm_bytes)
                    if (
                        voiced_signal_frames >= MIN_VOICED_FRAMES
                        and utterance_rms >= MIN_AUDIO_RMS
                    ):
                        for worker in workers:
                            worker.submit(pcm_bytes, utterance_ms)
                    else:
                        print(
                            f"[Compare] Discarded low-energy segment: "
                            f"utterance={utterance_ms:.0f}ms "
                            f"rms={utterance_rms:.0f} "
                            f"voiced_frames={voiced_signal_frames}"
                        )

                    speech_active = False
                    silence_bytes = 0
                    utterance_frames = []
                    voiced_frames = 0
                    voiced_signal_frames = 0
    except KeyboardInterrupt:
        print("\n[Compare] Stopping...")
    finally:
        for worker in workers:
            worker.stop()
        process.terminate()
        process.wait()


if __name__ == "__main__":
    main()
