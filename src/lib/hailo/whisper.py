"""Hailo Whisper client: VAD segmentation + hallucination/noise filtering.

Wraps hailo_platform.genai.Speech2Text with the pieces needed for reliable
real-time transcription on a continuously-listening mic:

- UtteranceSegmenter: turns a raw PCM stream into finished utterances using
  WebRTC VAD, with early/pause-based emission so long utterances don't wait
  for full silence before producing a result.
- WhisperClient: wraps Speech2Text itself, adding a repetition penalty
  (prevents hallucinated filler words on near-silence), a spectral pre-filter
  and crest-factor check (both computed only over VAD-flagged speech frames,
  not the whole buffer) to skip inference on keyboard clicks/footsteps/knocks
  without paying for a Whisper call, auto-gain for quiet mics, and
  post-processing deduplication for repeated/hallucinated sentences.

All thresholds below were tuned empirically against real usage logs, not
just theory - see the comment on each constant for what specifically drove
its value. Override any of them via the matching WHISPER_* env var.
"""
import os
import time
from pathlib import Path

import numpy as np
import webrtcvad

LIB_PATH = Path(__file__).parent.parent.resolve()
HAILO_MODELS_PATH = LIB_PATH / "hailo" / "models"

# WebRTC VAD (Voice Activity Detection) - frame-by-frame voice detection
# Aggressiveness: 0=most lenient (catches everything), 3=most aggressive (filters noise)
# Default 2 filters keyboard clicks while still catching speech
# Use 3 if getting false positives from typing/clicking, 1 for quiet speech
VAD_AGGRESSIVENESS = int(os.getenv("WHISPER_VAD_AGGRESSIVENESS", "2"))

# Frame size for VAD: must be 10ms, 20ms, or 30ms at 16kHz
# 20ms = 320 samples, good balance between latency and accuracy
VAD_FRAME_MS = 20


def _vad_frame_bytes(sample_rate: int) -> int:
    return int((sample_rate / 1000) * VAD_FRAME_MS * 2)


# Early transcription with pause-based breaking:
# 1. Collect speech until we have EARLY_TRANSCRIBE_MS (e.g., 2 seconds)
# 2. Then emit on first significant pause (PAUSE_TO_EMIT_MS)
# 3. Continue listening for more speech to append
# This gets fast response while respecting natural speech pauses
EARLY_TRANSCRIBE_MS = float(os.getenv("WHISPER_EARLY_TRANSCRIBE_MS", "2000"))  # Minimum speech before considering pause breaks
PAUSE_TO_EMIT_MS = float(os.getenv("WHISPER_PAUSE_TO_EMIT_MS", "400"))  # Brief pause triggers emission

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

# Threshold calibrated from real usage logs, not theory - even after
# restricting the ratio to VAD-flagged speech frames only, genuine
# continuous speech has measured as low as 0.10 (mic self-noise, room
# reverb, and breath noise outside the band all count against it), with
# most samples landing 0.10-0.29, while keyboard typing measured ~0.06.
# 0.45 and then 0.20 both still rejected real speech at the low end of its
# observed range. 0.08 sits just above the observed noise floor - this is
# a narrow margin (real speech and noise are not cleanly separable on this
# metric alone), so the crest-factor check below is now the primary
# defense against impulsive noise (knocks/clicks); band ratio mainly
# catches sustained broadband noise. Re-tune from your own printed ratios
# if real speech still gets skipped, or if noise starts passing through.
SPEECH_BAND_RATIO_THRESHOLD = float(os.getenv("WHISPER_SPEECH_BAND_RATIO_THRESHOLD", "0.08"))

# Crest factor (peak / RMS) pre-filter: catches impulsive transients (knocks,
# door taps, single claps) that pass the spectral filter above because their
# resonant frequency happens to fall inside the speech band. A knock is a
# sharp spike followed by fast decay - most of the buffer is near-silent
# ringdown - so its peak-to-RMS ratio is much higher than continuous
# phonation, where energy is spread more evenly across syllables.
# Typical continuous speech sits ~3-6; needs calibration against your mic/room.
CREST_FACTOR_MAX = float(os.getenv("WHISPER_CREST_FACTOR_MAX", "7.0"))


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
    frame_bytes = _vad_frame_bytes(sample_rate)
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
    F0+formant band. A low ratio here means "probably not speech" regardless
    of how VAD/duration classified it.

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

    def __init__(self, sample_rate: int, silence_timeout_ms: int, max_utterance_ms: int, min_speech_ms: float = MIN_SPEECH_MS, vad: webrtcvad.Vad = None, early_transcribe_ms: float = EARLY_TRANSCRIBE_MS, pause_to_emit_ms: float = PAUSE_TO_EMIT_MS, on_vad_change=None, on_drop=None, on_pause_emit=None):
        self._sample_rate = sample_rate
        self._silence_timeout_bytes = int(sample_rate * 2 * silence_timeout_ms / 1000)
        self._max_utterance_ms = max_utterance_ms
        self._min_speech_bytes = int(sample_rate * 2 * min_speech_ms / 1000)
        self._early_transcribe_bytes = int(sample_rate * 2 * early_transcribe_ms / 1000) if early_transcribe_ms > 0 else 0
        self._pause_to_emit_bytes = int(sample_rate * 2 * pause_to_emit_ms / 1000)
        self._vad = vad or webrtcvad.Vad(VAD_AGGRESSIVENESS)
        self._vad_frame_bytes = _vad_frame_bytes(sample_rate)

        # Optional diagnostics callbacks (e.g. for a CLI test harness to print
        # progress); left as no-ops so this class stays usable headless.
        self._on_vad_change = on_vad_change or (lambda is_speech: None)
        self._on_drop = on_drop or (lambda speech_ms, min_ms: None)
        self._on_pause_emit = on_pause_emit or (lambda speech_ms, pause_ms: None)

        self._speech_active = False
        self._silence_bytes = 0
        self._speech_bytes = 0
        self._frames = []
        self._start_time = 0.0
        self._vad_active = False
        self._ready_for_early_emit = False  # True after we have enough speech

    def process(self, data: bytes):
        """Feed one chunk of audio. Returns (pcm_bytes, utterance_ms) when
        an utterance just finished, otherwise None."""
        # Split into VAD frames and detect voice activity
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
            self._on_vad_change(vad_detected)

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
            self._on_pause_emit(self._speech_bytes / (self._sample_rate * 2) * 1000, self._silence_bytes / (self._sample_rate * 2) * 1000)
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
            self._on_drop(speech_duration_ms, min_duration_ms)
            return None

        return pcm_bytes, utterance_ms


class WhisperClient:
    """Wraps hailo_platform.genai.Speech2Text for whisper-on-HailoRT inference.

    Implements Hailo's best practices plus noise/hallucination filtering:
    - Repetition penalty to prevent hallucinations on near-silence
    - Spectral + crest-factor pre-filters to skip inference on keyboard
      clicks/footsteps/knocks (computed only over VAD-flagged speech frames)
    - Auto-gain adjustment for quiet audio
    - Post-processing deduplication for repeated/hallucinated sentences

    Shares the process-wide Hailo VDevice (lib/hailo/device.py) rather than
    opening its own - the Hailo-10H only exposes one physical device, so a
    second VDevice() call while another (e.g. Mind's HailoClient, or Ears)
    is open fails with HAILO_OUT_OF_PHYSICAL_DEVICES.
    """

    def __init__(self, hef_name: str, sample_rate: int, vad: webrtcvad.Vad = None):
        # Imported lazily (not at module level) so the segmentation/filter
        # helpers above stay importable/testable on machines without the
        # Hailo SDK installed - only constructing a WhisperClient itself
        # requires real Hailo hardware.
        from hailo_platform.genai import Speech2Text, Speech2TextTask

        from .device import get_vdevice

        hef_path = Path(hef_name)
        if not hef_path.is_absolute():
            hef_path = HAILO_MODELS_PATH / hef_name
        if not hef_path.is_file():
            raise FileNotFoundError(f"Hailo Whisper model not found at {hef_path}")

        self._sample_rate = sample_rate
        self._vad = vad or webrtcvad.Vad(VAD_AGGRESSIVENESS)
        self._task = Speech2TextTask.TRANSCRIBE
        self._vdevice = get_vdevice()
        self._s2t = Speech2Text(self._vdevice, str(hef_path))
        self._previous_texts = []  # Track last N transcriptions for deduplication

    def transcribe(self, pcm_bytes: bytes, on_filtered=None) -> str:
        """Transcribe audio with preprocessing and post-processing.

        Args:
            pcm_bytes: 16-bit mono PCM audio at self._sample_rate
            on_filtered: optional callback(reason: str, **metrics) called
                when audio is skipped before reaching Whisper - useful for a
                CLI harness to print diagnostics without this class doing I/O

        Returns:
            Cleaned transcription text, or "" if filtered/no speech found
        """
        on_filtered = on_filtered or (lambda reason, **metrics: None)

        # Convert to float32 normalized to [-1.0, 1.0)
        audio = np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float32) / 32768.0

        # Spectral + crest-factor pre-filter: skip Whisper entirely for
        # non-speech audio (keyboard clicks/footsteps/knocks). Cheaper than
        # an inference call and not fooled by duration the way VAD-based
        # gating alone is. Measured only over VAD-flagged speech frames, not
        # the whole buffer - a multi-second pause-based utterance includes
        # silence/pause padding that would otherwise dilute the ratio for
        # genuine speech.
        speech_only = extract_vad_speech(pcm_bytes, self._sample_rate, self._vad)
        ratio = speech_band_ratio(speech_only, self._sample_rate) if speech_only.size > 0 else 0.0
        cf = crest_factor(speech_only) if speech_only.size > 0 else 0.0

        if ratio < SPEECH_BAND_RATIO_THRESHOLD:
            on_filtered("not speech-like", band_ratio=ratio, threshold=SPEECH_BAND_RATIO_THRESHOLD, crest_factor=cf)
            return ""

        # Impulsive transient (knock/tap/clap) - passes the spectral filter
        # because its resonant energy overlaps the speech band, but its
        # peak-to-RMS shape gives it away as a spike-and-decay, not phonation.
        if cf > CREST_FACTOR_MAX:
            on_filtered("impulsive transient", crest_factor=cf, max=CREST_FACTOR_MAX)
            return ""

        # Auto-gain adjustment (Hailo recommendation for quiet mics)
        audio = improve_input_audio(audio)

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
        """Release the Speech2Text handle.

        Deliberately not releasing self._vdevice here: it is the shared
        process-wide HailoRT device (lib/hailo/device.py), also used by
        Mind's HailoClient and/or Ears - see Ears.stop_listening()'s comment
        for the same reasoning.
        """
        self._s2t.release()
