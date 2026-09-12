"""
Simple speech-to-text test: Whisper on HailoRT with hallucination prevention.

Listens to the mic continuously, segments speech with WebRTC VAD, and sends
utterances to Hailo Whisper. All the actual filtering/segmentation logic
lives in lib/whisper/client.py (UtteranceSegmenter, WhisperClient) - this
script is just a console harness that wires mic I/O to it and prints
diagnostics (dropped/skipped audio, latency).

Usage:
    python src/tests/whisper/simple.py

Env vars (all optional, see src/config.py for the same names used elsewhere;
see lib/whisper/client.py for the full rationale behind each default):
    HAILO_WHISPER_MODEL_HEF         Whisper HEF file name under lib/hailo/models
                                    (required; e.g. "Whisper-Small.hef")
    MIC_DEVICE                      arecord -D device string, e.g. "plughw:0,0"
    WHISPER_SAMPLE_RATE             Mic sample rate, default 16000 (model requirement)
    WHISPER_VAD_AGGRESSIVENESS      WebRTC VAD aggressiveness (0-3, default 2)
    WHISPER_EARLY_TRANSCRIBE_MS     Minimum speech before considering pause breaks, default 2000ms
    WHISPER_PAUSE_TO_EMIT_MS        Pause duration that triggers early emission, default 400ms
    WHISPER_MIN_SPEECH_MS           Minimum speech duration before transcribing, default 500ms
    WHISPER_REPETITION_PENALTY      Hallucination prevention factor, default 1.5
    WHISPER_SPEECH_BAND_RATIO_THRESHOLD  Spectral pre-filter threshold, default 0.20
    WHISPER_CREST_FACTOR_MAX        Crest-factor pre-filter max, default 7.0
"""

import os
import subprocess
import sys
import time
from pathlib import Path

# Anchor to project root (src) so `config` and `lib` resolve like other tests.
PROJECT_PATH = Path(__file__).parent.parent.parent.resolve()
if str(PROJECT_PATH) not in sys.path:
    sys.path.insert(0, str(PROJECT_PATH))

from config import Env
from lib.hailo.whisper import (
    CREST_FACTOR_MAX,
    EARLY_TRANSCRIBE_MS,
    MIN_SPEECH_MS,
    PAUSE_TO_EMIT_MS,
    REPETITION_PENALTY,
    SPEECH_BAND_RATIO_THRESHOLD,
    VAD_AGGRESSIVENESS,
    UtteranceSegmenter,
    WhisperClient,
)

SAMPLE_RATE = Env.WhisperSampleRate
MIC_DEVICE = os.getenv("MIC_DEVICE")

# Utterance segmentation
READ_CHUNK_MS = 80
READ_CHUNK_BYTES = int((SAMPLE_RATE / 1000) * READ_CHUNK_MS * 2)
SILENCE_TIMEOUT_MS = 500
MAX_UTTERANCE_MS = 15_000


def start_mic(sample_rate: int, device: str | None) -> subprocess.Popen:
    cmd = ["arecord", "-f", "S16_LE", "-r", str(sample_rate), "-c", "1", "-t", "raw"]
    if device:
        cmd[1:1] = ["-D", device]
    try:
        return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=READ_CHUNK_BYTES)
    except FileNotFoundError:
        print("[ERROR] arecord not found. Install alsa-utils: apt install alsa-utils")
        sys.exit(1)


def on_drop(speech_ms: float, min_ms: float):
    print(f"[Segmenter] Dropped short utterance ({speech_ms:.0f}ms, min {min_ms:.0f}ms)")


def on_pause_emit(speech_ms: float, pause_ms: float):
    print(f"[Segmenter] Pause-based emit ({speech_ms:.0f}ms speech, {pause_ms:.0f}ms pause)")


def on_filtered(reason: str, **metrics):
    details = ", ".join(f"{k}={v:.2f}" for k, v in metrics.items())
    print(f"[Whisper] Skipped - {reason} ({details})")


def main():
    whisper_model_name = os.getenv("HAILO_WHISPER_MODEL_HEF")
    if not whisper_model_name:
        print("[ERROR] HAILO_WHISPER_MODEL_HEF is not set.")
        print("       Set environment variable, e.g.: export HAILO_WHISPER_MODEL_HEF=Whisper-Small.hef")
        sys.exit(1)

    try:
        engine = WhisperClient(whisper_model_name, sample_rate=SAMPLE_RATE)
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
        early_transcribe_ms=EARLY_TRANSCRIBE_MS,
        pause_to_emit_ms=PAUSE_TO_EMIT_MS,
        on_drop=on_drop,
        on_pause_emit=on_pause_emit,
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
                text = engine.transcribe(pcm_bytes, on_filtered=on_filtered)
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
