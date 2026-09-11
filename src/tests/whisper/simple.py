"""
Simple speech-to-text test: Whisper on HailoRT with hallucination prevention.

Listens to the mic continuously, gates out silence/noise with VAD (Voice Activity
Detection), applies auto-gain normalization, and sends speech to Hailo Whisper.
Implements Hailo's best practices for real-time inference:
- Repetition penalty (1.5) to prevent hallucinations on silence/noise
- Energy-based VAD with automatic gain adjustment
- Post-processing deduplication for repeated sentences
- Timestamps and latency reporting for monitoring

Usage:
    python src/tests/whisper/simple.py

Env vars (all optional, see src/config.py for the same names used elsewhere):
    HAILO_WHISPER_MODEL_HEF   Whisper HEF file name under lib/hailo/models
                              (required; e.g. "Whisper-Small.hef")
    MIC_DEVICE                arecord -D device string, e.g. "plughw:0,0"
    WHISPER_SAMPLE_RATE       Mic sample rate, default 16000 (model requirement)
    WHISPER_NOISE_GATE_DBFS   VAD energy threshold, default -45.0 dBFS
                              (lower = more sensitive, 0.2 energy normalized)
    WHISPER_MIN_SPEECH_MS     Minimum gated-open speech before sending to model,
                              default 500ms (prevents short noise blips)
    WHISPER_REPETITION_PENALTY Hallucination prevention factor, default 1.5
                              (higher = more aggressive, 1.5-2.0 typical range)
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

# VAD (Voice Activity Detection) configuration
# Energy-based threshold: 0.2 is Hailo's recommended default (0.15-0.25 tunable)
# Mapped from dBFS for backwards compatibility with existing config
NOISE_GATE_DBFS = float(os.getenv("WHISPER_NOISE_GATE_DBFS", "-45.0"))
NOISE_GATE_ENERGY = 0.2  # Normalized energy (0.0-1.0) from Hailo recommendation

# Minimum speech duration before sending to model
# Prevents short noise blips from triggering false transcriptions
MIN_SPEECH_MS = float(os.getenv("WHISPER_MIN_SPEECH_MS", "500"))

# Hallucination prevention: repetition penalty factor
# Hailo's default is 1.5 (prevents silent audio hallucination)
# Increase to 2.0+ if hallucinations persist in your environment
REPETITION_PENALTY = float(os.getenv("WHISPER_REPETITION_PENALTY", "1.5"))


def rms_dbfs(data: bytes) -> float:
    """RMS level of 16-bit PCM audio, in dBFS (0 dBFS = full scale)."""
    samples = np.frombuffer(data, dtype=np.int16).astype(np.float32)
    if samples.size == 0:
        return -float("inf")
    rms = np.sqrt(np.mean(np.square(samples)))
    if rms <= 0:
        return -float("inf")
    return 20 * np.log10(rms / 32768.0)


def improve_input_audio(audio: np.ndarray) -> np.ndarray:
    """Automatic gain adjustment for quiet audio (Hailo recommendation).

    Whisper is sensitive to input levels. This applies:
    - +20dB gain if peak amplitude < 0.1
    - +10dB gain if peak amplitude < 0.2
    - Otherwise no adjustment

    Args:
        audio: float32 PCM audio normalized to [-1.0, 1.0)

    Returns:
        Gain-adjusted audio, still in [-1.0, 1.0) range
    """
    peak = np.abs(audio).max()
    if peak < 0.1:
        audio = audio * 10.0  # +20dB
    elif peak < 0.2:
        audio = audio * 3.16  # +10dB
    return np.clip(audio, -1.0, 0.9999)


def clean_transcription(text: str, previous_texts: list[str] = None) -> str:
    """Remove repeated/hallucinated sentences (Hailo post-processing).

    Whisper sometimes repeats or hallucinates sentences from silence.
    This deduplicates based on normalized text comparison.

    Args:
        text: Current transcription
        previous_texts: List of prior transcriptions to check against

    Returns:
        Cleaned text with deduplicated sentences
    """
    if not text or not previous_texts:
        return text

    sentences = [s.strip() for s in text.split(".") if s.strip()]
    cleaned = []

    for sentence in sentences:
        normalized = sentence.lower().strip()
        # Check if this sentence (or a substring) appeared before
        is_duplicate = any(
            normalized in prev.lower() or prev.lower() in normalized
            for prev in previous_texts
        )
        if not is_duplicate:
            cleaned.append(sentence)

    return ". ".join(cleaned) + ("." if cleaned and text.endswith(".") else "")


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
    """Wraps hailo_platform.genai.Speech2Text for whisper-on-HailoRT inference.

    Implements Hailo's best practices:
    - Repetition penalty to prevent hallucinations
    - Auto-gain adjustment for quiet audio
    - Post-processing deduplication
    """

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
        self._s2t = Speech2Text(
            self._vdevice,
            str(hef_path),
            repetition_penalty=REPETITION_PENALTY,  # Prevent silent hallucinations
        )
        print(f"[Hailo] Model '{hef_path.name}' ready (repetition_penalty={REPETITION_PENALTY})")
        self._previous_texts = []  # Track last N transcriptions for deduplication

    def transcribe(self, pcm_bytes: bytes) -> str:
        """Transcribe audio with preprocessing and post-processing.

        Args:
            pcm_bytes: 16-bit mono PCM audio at SAMPLE_RATE

        Returns:
            Cleaned transcription text
        """
        # Convert to float32 normalized to [-1.0, 1.0)
        audio = np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float32) / 32768.0

        # Auto-gain adjustment (Hailo recommendation for quiet mics)
        audio = improve_input_audio(audio)

        # Hailo's Speech2Text expects exact sample rate (16kHz)
        text = self._s2t.generate_all_text(
            audio_data=audio,
            task=self._task,
            language="en"
        ).strip()

        # Post-processing: deduplicate against recent history
        if text:
            text = clean_transcription(text, self._previous_texts[-3:])  # Check last 3

        # Track for next deduplication check
        if text:
            self._previous_texts.append(text)
            if len(self._previous_texts) > 10:
                self._previous_texts.pop(0)

        return text

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
        print("       Set environment variable, e.g.: export HAILO_WHISPER_MODEL_HEF=Whisper-Small.hef")
        sys.exit(1)

    try:
        engine = HailoWhisperEngine(whisper_model_name)
    except FileNotFoundError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Failed to initialize Hailo: {e}")
        print("       Check: hailo_platform installed, Python version matches wheel (cp313/3.13)")
        sys.exit(1)

    segmenter = UtteranceSegmenter(SAMPLE_RATE, SILENCE_TIMEOUT_MS, MAX_UTTERANCE_MS, min_speech_ms=MIN_SPEECH_MS)
    process = start_mic(SAMPLE_RATE, MIC_DEVICE)

    print(f"[Whisper] Listening on {SAMPLE_RATE}Hz...")
    print(f"[Whisper] Config: VAD threshold {NOISE_GATE_DBFS} dBFS, min speech {MIN_SPEECH_MS:.0f}ms, repetition_penalty {REPETITION_PENALTY}")
    print("[Whisper] (Ctrl+C to stop)\n")

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
                print(f"[Whisper ERROR] Inference failed: {e}")
                continue
            latency_ms = (time.time() - start) * 1000

            if text:
                print(f"[Whisper] speech={utterance_ms:.0f}ms latency={latency_ms:.0f}ms: {text}")
            else:
                print(f"[Whisper] speech={utterance_ms:.0f}ms latency={latency_ms:.0f}ms: (no speech)")

    except KeyboardInterrupt:
        print("\n[Whisper] Stopping...")
    except Exception as e:
        print(f"\n[Whisper FATAL] {e}")
        import traceback
        traceback.print_exc()
    finally:
        engine.stop()
        process.terminate()
        try:
            process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


if __name__ == "__main__":
    main()
