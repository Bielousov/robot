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
    HAILO_WHISPER_MODEL_HEF         Whisper HEF file name under lib/hailo/models
                                    (required; e.g. "Whisper-Small.hef")
    MIC_DEVICE                      arecord -D device string, e.g. "plughw:0,0"
    WHISPER_SAMPLE_RATE             Mic sample rate, default 16000 (model requirement)
    WHISPER_VAD_AGGRESSIVENESS      WebRTC VAD aggressiveness (0-3, default 2)
                                    0=lenient, 3=aggressive at filtering non-speech
    WHISPER_EARLY_TRANSCRIBE_MS     Start transcribing after N ms of speech, default 2000ms
                                    Reduces latency by transcribing while still listening
                                    Set to 0 to wait for silence detection instead
    WHISPER_MIN_SPEECH_MS           Minimum speech duration before sending to model,
                                    default 500ms (prevents isolated noise)
    WHISPER_REPETITION_PENALTY      Hallucination prevention factor, default 1.5
                                    (higher = more aggressive, 1.5-2.0 typical range)
    WHISPER_SPEECH_BAND_RATIO_THRESHOLD  Fraction of energy required in the
                                    80-4000Hz band (voice F0 + harmonics +
                                    sibilants), default 0.45. Filters keyboard
                                    clicks/footsteps (broadband transients) that
                                    VAD duration alone can't distinguish from
                                    real speech. Lower = more lenient, raise if
                                    clicks still get through. Measured only over
                                    VAD-flagged speech frames (not the whole
                                    buffer) so pause/silence padding in a
                                    multi-second utterance doesn't dilute it.
    WHISPER_CREST_FACTOR_MAX        Max peak-to-RMS ratio allowed, default 7.0.
                                    Catches impulsive transients (knocks, taps,
                                    claps) that pass the spectral filter above
                                    because their resonance overlaps the speech
                                    band - their spike-then-decay shape gives a
                                    much higher crest factor than sustained
                                    phonation. Lower = stricter, raise if normal
                                    speech (e.g. plosives "p"/"t"/"k") gets
                                    rejected.
"""

import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import webrtcvad

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

# Early transcription with pause-based breaking:
# 1. Collect speech until we have EARLY_TRANSCRIBE_MS (e.g., 2 seconds)
# 2. Then emit on first significant pause (PAUSE_TO_EMIT_MS)
# 3. Continue listening for more speech to append
# This gets fast response while respecting natural speech pauses
EARLY_TRANSCRIBE_MS = float(os.getenv("WHISPER_EARLY_TRANSCRIBE_MS", "2000"))  # Minimum speech before considering pause breaks
PAUSE_TO_EMIT_MS = float(os.getenv("WHISPER_PAUSE_TO_EMIT_MS", "400"))  # Brief pause (300ms) triggers emission

# WebRTC VAD (Voice Activity Detection) - frame-by-frame voice detection
# Aggressiveness: 0=most lenient (catches everything), 3=most aggressive (filters noise)
# Default 2 filters keyboard clicks while still catching speech
# Use 3 if getting false positives from typing/clicking, 1 for quiet speech
VAD_AGGRESSIVENESS = int(os.getenv("WHISPER_VAD_AGGRESSIVENESS", "2"))
VAD = webrtcvad.Vad(VAD_AGGRESSIVENESS)

# Frame size for VAD: must be 10ms, 20ms, or 30ms at 16kHz
# 20ms = 320 samples, good balance between latency and accuracy
VAD_FRAME_MS = 20
VAD_FRAME_BYTES = int((SAMPLE_RATE / 1000) * VAD_FRAME_MS * 2)

# Minimum speech duration before sending to model
# Prevents isolated noise from triggering transcription
MIN_SPEECH_MS = float(os.getenv("WHISPER_MIN_SPEECH_MS", "500"))

# Hallucination prevention: repetition penalty factor
# Hailo's default is 1.5 (prevents silent audio hallucination)
# Increase to 2.0+ if hallucinations persist in your environment
REPETITION_PENALTY = float(os.getenv("WHISPER_REPETITION_PENALTY", "1.5"))

# Spectral pre-filter: distinguishes speech from keyboard clicks/footsteps.
# Duration alone doesn't work - repeated clicks toggle VAD on/off and can
# accumulate the same total duration as real speech. Instead, check where
# the audio's energy actually is: clicks/footsteps are broadband transients
# (impact noise) without the fundamental+harmonic structure of a voice.
#
# Lower bound is 80Hz, not the "telephone band" 300Hz - male fundamental
# frequency (F0) commonly sits at 85-180Hz, female at 165-255Hz, so a 300Hz
# floor excludes F0 and its lowest harmonics for most speakers, undercounting
# real speech energy and tanking the ratio (measured ~0.15 on real speech
# before this fix). Upper bound extended to 4000Hz to include sibilants
# ("s", "sh", "f") which carry meaningful energy above 3400Hz.
SPEECH_BAND_LOW_HZ = 80
SPEECH_BAND_HIGH_HZ = 4000
SPEECH_BAND_RATIO_THRESHOLD = float(os.getenv("WHISPER_SPEECH_BAND_RATIO_THRESHOLD", "0.45"))

# Crest factor (peak / RMS) pre-filter: catches impulsive transients (knocks,
# door taps, single claps) that pass the spectral filter above because their
# resonant frequency happens to fall inside the speech band. A knock is a
# sharp spike followed by fast decay - most of the buffer is near-silent
# ringdown - so its peak-to-RMS ratio is much higher than continuous
# phonation, where energy is spread more evenly across syllables.
# Typical continuous speech sits ~3-6; needs calibration against your mic/room.
CREST_FACTOR_MAX = float(os.getenv("WHISPER_CREST_FACTOR_MAX", "7.0"))


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


def extract_vad_speech(pcm_bytes: bytes, sample_rate: int, vad: webrtcvad.Vad) -> np.ndarray:
    """Concatenate only the VAD-flagged speech portions of a PCM buffer.

    A pause-based/early-transcribe buffer spans several seconds and includes
    the silence/pause gaps between phrases (breathing, room tone, mic noise)
    alongside the actual speech. Computing the spectral ratio over the whole
    buffer lets that padding dilute the score - a real multi-second utterance
    can end up scoring as "not speech-like" purely because a large fraction
    of its bytes are near-silent gaps, not because the speech itself is
    atypical. Restricting the ratio to only the VAD-active frames removes
    that dilution.

    Args:
        pcm_bytes: 16-bit mono PCM audio at sample_rate
        sample_rate: audio sample rate in Hz
        vad: WebRTC VAD instance to classify each frame

    Returns:
        float32 audio normalized to [-1.0, 1.0) containing only speech-flagged
        frames concatenated together (empty array if none found)
    """
    frame_bytes = VAD_FRAME_BYTES
    speech_chunks = []
    offset = 0
    while offset + frame_bytes <= len(pcm_bytes):
        frame = pcm_bytes[offset : offset + frame_bytes]
        if vad.is_speech(frame, sample_rate):
            speech_chunks.append(frame)
        offset += frame_bytes

    if not speech_chunks:
        return np.array([], dtype=np.float32)

    speech_bytes = b"".join(speech_chunks)
    return np.frombuffer(speech_bytes, dtype=np.int16).astype(np.float32) / 32768.0


def speech_band_ratio(audio: np.ndarray, sample_rate: int, low_hz: float = SPEECH_BAND_LOW_HZ, high_hz: float = SPEECH_BAND_HIGH_HZ) -> float:
    """Fraction of audio energy inside the human speech formant band.

    Keyboard clicks and footsteps are broadband transients (impact noise
    spread across all frequencies, often with a strong high-frequency
    component). Voiced speech concentrates most of its energy in the
    ~300-3400Hz formant band. A low ratio here means "probably not speech"
    regardless of how VAD/duration classified it.

    Args:
        audio: float32 PCM audio normalized to [-1.0, 1.0)
        sample_rate: audio sample rate in Hz

    Returns:
        Ratio in [0.0, 1.0]; 0.0 for empty/silent audio
    """
    if audio.size == 0:
        return 0.0

    spectrum = np.abs(np.fft.rfft(audio))
    total_energy = np.sum(spectrum ** 2)
    if total_energy <= 0:
        return 0.0

    freqs = np.fft.rfftfreq(audio.size, d=1.0 / sample_rate)
    band_mask = (freqs >= low_hz) & (freqs <= high_hz)
    band_energy = np.sum(spectrum[band_mask] ** 2)

    return float(band_energy / total_energy)


def crest_factor(audio: np.ndarray) -> float:
    """Peak-to-RMS amplitude ratio.

    Sharp transients (knocks, taps, claps) have a brief spike followed by
    near-silent decay, giving a high ratio. Continuous speech phonation
    spreads energy more evenly across syllables, giving a lower ratio even
    when its frequency content overlaps the speech band.

    Args:
        audio: float32 PCM audio normalized to [-1.0, 1.0)

    Returns:
        Ratio >= 1.0; 0.0 for empty/silent audio
    """
    if audio.size == 0:
        return 0.0
    rms = np.sqrt(np.mean(np.square(audio)))
    if rms <= 0:
        return 0.0
    peak = np.abs(audio).max()
    return float(peak / rms)


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
    """Turns a stream of raw PCM chunks into finished utterances using WebRTC VAD."""

    def __init__(self, sample_rate: int, silence_timeout_ms: int, max_utterance_ms: int, min_speech_ms: float = 0, vad: webrtcvad.Vad = None, early_transcribe_ms: float = 0, pause_to_emit_ms: float = 300):
        self._sample_rate = sample_rate
        self._silence_timeout_bytes = int(sample_rate * 2 * silence_timeout_ms / 1000)
        self._max_utterance_ms = max_utterance_ms
        self._min_speech_bytes = int(sample_rate * 2 * min_speech_ms / 1000)
        self._early_transcribe_bytes = int(sample_rate * 2 * early_transcribe_ms / 1000) if early_transcribe_ms > 0 else 0
        self._pause_to_emit_bytes = int(sample_rate * 2 * pause_to_emit_ms / 1000)
        self._vad = vad or VAD
        self._vad_frame_bytes = VAD_FRAME_BYTES

        self._speech_active = False
        self._silence_bytes = 0
        self._speech_bytes = 0
        self._frames = []
        self._start_time = 0.0
        self._vad_active = False
        self._ready_for_early_emit = False  # True after we have enough speech

    def process(self, data: bytes):
        """Feed one chunk of audio (80ms). Returns (pcm_bytes, utterance_ms) when
        an utterance just finished, otherwise None."""
        # Split into VAD frames (20ms each) and detect voice activity
        vad_detected = False
        offset = 0
        while offset + self._vad_frame_bytes <= len(data):
            frame = data[offset : offset + self._vad_frame_bytes]
            if self._vad.is_speech(frame, self._sample_rate):
                vad_detected = True
                break
            offset += self._vad_frame_bytes

        if vad_detected != self._vad_active:
            self._vad_active = vad_detected
            print(f"[VAD] {'speech' if vad_detected else 'silence'} detected")

        if vad_detected:
            if not self._speech_active:
                self._start_time = time.time()
                self._speech_bytes = 0
            self._speech_active = True
            self._silence_bytes = 0
            self._speech_bytes += len(data)
            self._frames.append(data)

            # Mark ready for early emission once we have enough speech
            if self._early_transcribe_bytes > 0 and self._speech_bytes >= self._early_transcribe_bytes:
                self._ready_for_early_emit = True

            return None

        if not self._speech_active:
            return None

        # Pause detected - check if we should emit for early transcription
        self._silence_bytes += len(data)
        self._frames.append(data)

        # If we have enough speech and a brief pause, emit for transcription
        # (don't wait for full silence timeout)
        if self._ready_for_early_emit and self._silence_bytes >= self._pause_to_emit_bytes:
            print(f"[Segmenter] Pause-based emit ({self._speech_bytes / (self._sample_rate * 2) * 1000:.0f}ms speech, {self._silence_bytes / (self._sample_rate * 2) * 1000:.0f}ms pause)")
            result = self._finalize_utterance()
            self._ready_for_early_emit = False
            return result

        elapsed_ms = (time.time() - self._start_time) * 1000
        silence_timeout = self._silence_bytes >= self._silence_timeout_bytes
        if not (silence_timeout or elapsed_ms >= self._max_utterance_ms):
            return None

        return self._finalize_utterance()

    def _finalize_utterance(self):
        """Finalize the current utterance and return it, or None if too short."""
        pcm_bytes = b"".join(self._frames)
        utterance_ms = (time.time() - self._start_time) * 1000
        speech_bytes = self._speech_bytes

        self._speech_active = False
        self._silence_bytes = 0
        self._speech_bytes = 0
        self._frames = []

        if speech_bytes < self._min_speech_bytes:
            speech_duration_ms = speech_bytes / (self._sample_rate * 2) * 1000
            min_duration_ms = self._min_speech_bytes / (self._sample_rate * 2) * 1000
            print(f"[Segmenter] Dropped short utterance ({speech_duration_ms:.0f}ms, min {min_duration_ms:.0f}ms)")
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
        self._s2t = Speech2Text(self._vdevice, str(hef_path))
        print(f"[Hailo] Model '{hef_path.name}' ready (will use repetition_penalty={REPETITION_PENALTY} during inference)")
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

        # Spectral pre-filter: skip Whisper entirely for non-speech audio
        # (keyboard clicks/footsteps have broadband energy, not concentrated
        # in the speech formant band). Cheaper than an inference call and not
        # fooled by duration the way VAD-based gating is.
        #
        # Measured only over VAD-flagged speech frames, not the whole buffer -
        # a multi-second pause-based utterance includes silence/pause padding
        # that would otherwise dilute the ratio for genuine speech.
        speech_only = extract_vad_speech(pcm_bytes, SAMPLE_RATE, VAD)
        ratio = speech_band_ratio(speech_only, SAMPLE_RATE) if speech_only.size > 0 else 0.0
        cf = crest_factor(speech_only) if speech_only.size > 0 else 0.0

        if ratio < SPEECH_BAND_RATIO_THRESHOLD:
            print(f"[Whisper] Skipped - not speech-like (band ratio={ratio:.2f}, threshold={SPEECH_BAND_RATIO_THRESHOLD:.2f})")
            return ""

        # Impulsive transient (knock/tap/clap) - passes the spectral filter
        # because its resonant energy overlaps the speech band, but its
        # peak-to-RMS shape gives it away as a spike-and-decay, not phonation.
        if cf > CREST_FACTOR_MAX:
            print(f"[Whisper] Skipped - impulsive transient (crest factor={cf:.1f}, max={CREST_FACTOR_MAX:.1f})")
            return ""

        # Auto-gain adjustment (Hailo recommendation for quiet mics)
        audio = improve_input_audio(audio)

        # Hailo's Speech2Text expects exact sample rate (16kHz)
        try:
            text = self._s2t.generate_all_text(
                audio_data=audio,
                task=self._task,
                language="en",
                repetition_penalty=REPETITION_PENALTY
            ).strip()
        except TypeError:
            # Fallback if repetition_penalty not supported in this version
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

    segmenter = UtteranceSegmenter(
        SAMPLE_RATE, SILENCE_TIMEOUT_MS, MAX_UTTERANCE_MS,
        min_speech_ms=MIN_SPEECH_MS,
        vad=VAD,
        early_transcribe_ms=EARLY_TRANSCRIBE_MS,
        pause_to_emit_ms=PAUSE_TO_EMIT_MS
    )
    process = start_mic(SAMPLE_RATE, MIC_DEVICE)

    print(f"[Whisper] Listening on {SAMPLE_RATE}Hz...")
    print(f"[Whisper] Config: VAD aggressiveness={VAD_AGGRESSIVENESS}, early transcribe after {EARLY_TRANSCRIBE_MS:.0f}ms, pause emit {PAUSE_TO_EMIT_MS:.0f}ms")
    print(f"[Whisper] Repetition penalty={REPETITION_PENALTY}, min speech {MIN_SPEECH_MS:.0f}ms")
    print(f"[Whisper] Speech-band ratio threshold={SPEECH_BAND_RATIO_THRESHOLD:.2f} (filters clicks/footsteps)")
    print(f"[Whisper] Crest factor max={CREST_FACTOR_MAX:.1f} (filters knocks/taps/claps)")
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
            print(f"[Segmenter] Utterance detected ({utterance_ms:.0f}ms), transcribing...")
            start = time.time()
            try:
                text = engine.transcribe(pcm_bytes)
            except Exception as e:
                print(f"[Whisper ERROR] Inference failed: {e}")
                import traceback
                traceback.print_exc()
                continue
            latency_ms = (time.time() - start) * 1000

            if text:
                print(f"[Whisper] speech={utterance_ms:.0f}ms latency={latency_ms:.0f}ms: {text}")
            else:
                print(f"[Whisper] speech={utterance_ms:.0f}ms latency={latency_ms:.0f}ms: (no speech detected)")

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
