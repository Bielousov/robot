"""
Simple speech-to-text test: Whisper on HailoRT only.

Listens to the mic continuously, gates out silence/noise with a plain RMS
noise gate (Whisper's acoustic model is sensitive enough that quiet
hums/electrical noise get transcribed as hallucinated text rather than
rejected outright), and prints each utterance's transcript plus timing
(utterance length, inference latency) to the console.

Usage:
    python src/tests/whisper/simple.py

Env vars (all optional, see src/config.py for the same names used elsewhere):
    HAILO_WHISPER_MODEL_HEF   Whisper HEF file name under lib/hailo/models
                              (required; e.g. "Whisper-Small.hef")
    MIC_DEVICE                arecord -D device string, e.g. "plughw:0,0"
    WHISPER_SAMPLE_RATE       Mic sample rate, default 16000
    WHISPER_NOISE_GATE_DBFS   RMS noise gate threshold, default -45.0
    WHISPER_MIN_SPEECH_MS     Minimum gated-open speech before an utterance
                              is sent to Whisper, default 500
"""

import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

# Anchor to project root (src) so `config` and `lib` resolve like other tests.
PROJECT_PATH = Path(__file__).parent.parent.parent.resolve()
if str(PROJECT_PATH) not in sys.path:
    sys.path.insert(0, str(PROJECT_PATH))

from config import Env

HAILO_MODELS_PATH = PROJECT_PATH / "lib" / "hailo" / "models"

SAMPLE_RATE = Env.WhisperSampleRate
MIC_DEVICE = os.getenv("MIC_DEVICE")

# Utterance segmentation
READ_CHUNK_MS = 80
READ_CHUNK_BYTES = int((SAMPLE_RATE / 1000) * READ_CHUNK_MS * 2)
SILENCE_TIMEOUT_MS = 500
MAX_UTTERANCE_MS = 15_000

# Whisper noise gate: a plain RMS/dBFS threshold instead of a speech
# classifier. -55 dBFS is a starting point for mic setups with no
# hardware/AGC gain; watch the "[Whisper Gate]" transitions printed at
# runtime and raise/lower WHISPER_NOISE_GATE_DBFS to match your input level.
NOISE_GATE_DBFS = float(os.getenv("WHISPER_NOISE_GATE_DBFS", "-45.0"))

# Whisper hallucinates filler words ("So,", "You", "The") when fed a
# sliver of near-silence/noise rather than real speech - a single noise
# blip that briefly crosses the gate is enough to trigger this. Require at
# least this much actual gated-open audio (not counting the silence tail)
# before an utterance is sent to Whisper at all.
MIN_SPEECH_MS = float(os.getenv("WHISPER_MIN_SPEECH_MS", "500"))


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
    """Turns a stream of raw PCM chunks into finished utterances, gated by
    a simple RMS noise gate."""

    def __init__(self, sample_rate: int, silence_timeout_ms: int, max_utterance_ms: int, min_speech_ms: float = 0):
        self._sample_rate = sample_rate
        self._silence_timeout_bytes = int(sample_rate * 2 * silence_timeout_ms / 1000)
        self._max_utterance_ms = max_utterance_ms
        self._min_speech_bytes = int(sample_rate * 2 * min_speech_ms / 1000)

        self._speech_active = False
        self._silence_bytes = 0
        self._speech_bytes = 0
        self._frames = []
        self._start_time = 0.0
        self._gate_open = False

    def process(self, data: bytes):
        """Feed one chunk of audio. Returns (pcm_bytes, utterance_ms) when
        an utterance just finished, otherwise None."""
        level = rms_dbfs(data)
        has_speech = level >= NOISE_GATE_DBFS

        if has_speech != self._gate_open:
            self._gate_open = has_speech
            state = "open" if has_speech else "closed"
            print(f"[Whisper Gate] {state} ({level:.1f} dBFS, threshold {NOISE_GATE_DBFS:.1f})")

        if has_speech:
            if not self._speech_active:
                self._start_time = time.time()
                self._speech_bytes = 0
            self._speech_active = True
            self._silence_bytes = 0
            self._speech_bytes += len(data)
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
        speech_bytes = self._speech_bytes

        self._speech_active = False
        self._silence_bytes = 0
        self._speech_bytes = 0
        self._frames = []

        if speech_bytes < self._min_speech_bytes:
            print(f"[Whisper Gate] dropped short utterance ({speech_bytes / (self._sample_rate * 2) * 1000:.0f}ms speech)")
            return None

        return pcm_bytes, utterance_ms


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
    whisper_model_name = os.getenv("HAILO_WHISPER_MODEL_HEF")
    if not whisper_model_name:
        print("[ERROR] HAILO_WHISPER_MODEL_HEF is not set.")
        sys.exit(1)

    engine = HailoWhisperEngine(whisper_model_name)
    segmenter = UtteranceSegmenter(SAMPLE_RATE, SILENCE_TIMEOUT_MS, MAX_UTTERANCE_MS, min_speech_ms=MIN_SPEECH_MS)
    process = start_mic(SAMPLE_RATE, MIC_DEVICE)

    print(f"[Compare] Listening on {SAMPLE_RATE}Hz... (Ctrl+C to stop)")

    try:
        while True:
            data = process.stdout.read(READ_CHUNK_BYTES)
            if not data:
                break

            utterance = segmenter.process(data)
            if not utterance:
                continue

            pcm_bytes, utterance_ms = utterance
            start = time.time()
            try:
                text = engine.transcribe(pcm_bytes)
            except Exception as e:
                print(f"[Whisper/Hailo] error: {e}")
                continue
            latency_ms = (time.time() - start) * 1000

            if text:
                print(f"[Whisper/Hailo] utterance={utterance_ms:.0f}ms latency={latency_ms:.0f}ms: {text}")
            else:
                print(f"[Whisper/Hailo] utterance={utterance_ms:.0f}ms latency={latency_ms:.0f}ms: (no speech recognized)")
    except KeyboardInterrupt:
        print("\n[Compare] Stopping...")
    finally:
        engine.stop()
        process.terminate()
        process.wait()


if __name__ == "__main__":
    main()
