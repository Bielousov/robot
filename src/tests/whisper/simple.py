import subprocess
import torch
import numpy as np
from pathlib import Path
from silero_vad import load_silero_vad, get_speech_timestamps
from faster_whisper import WhisperModel

# -----------------------------
# Load Silero VAD model
# -----------------------------
vad_model = load_silero_vad()

# Path to whisper model
WHISPER_MODEL_PATH = Path(__file__).parent.parent.parent / "lib" / "whisper" / "models" / "ggml-small.en.bin"

if not WHISPER_MODEL_PATH.exists():
    print(f"[WARNING] Whisper model not found at {WHISPER_MODEL_PATH}, will download")

# Load faster-whisper model (use "base" model size, not local file path)
print("Loading Whisper model...")
whisper_model = WhisperModel("base", device="cpu", compute_type="int8")

# -----------------------------
# Start arecord (16kHz mono PCM)
# -----------------------------
arecord_cmd = [
    "arecord",
    "-D", "capture",
    "-f", "S16_LE",
    "-r", "16000",
    "-c", "1"
]
process = subprocess.Popen(arecord_cmd, stdout=subprocess.PIPE, bufsize=0)

# -----------------------------
# Read and process audio buffer
# -----------------------------
buffer_size = 4000  # samples
audio_buffer = []

try:
    while True:
        raw_data = process.stdout.read(buffer_size * 2)  # 2 bytes per sample
        if not raw_data:
            break

        # Convert to float32 tensor [-1, 1]
        audio = torch.frombuffer(raw_data, dtype=torch.int16).float() / 32768.0
        # Make a copy to avoid the non-writable buffer warning
        audio = audio.clone()

        audio_buffer.append(audio)

        # Combine buffer for VAD
        combined = torch.cat(audio_buffer)

        # Run VAD
        speech = get_speech_timestamps(combined, vad_model, sampling_rate=16000)

        if speech:
            print("Speech detected")
            print(f"[DEBUG] Speech timestamps: start={speech[0]['start']:.0f}, end={speech[0]['end']:.0f}")
            print(f"[DEBUG] Combined buffer length: {len(combined)} samples ({len(combined) / 16000:.4f}s)")
            
            # Extract the speech segment using proper indexing
            # VAD returns timestamps in SAMPLES, not seconds
            speech_start = max(0, int(speech[0]['start']))
            speech_end = min(len(combined), int(speech[0]['end']))
            
            print(f"[DEBUG] Extracted indices: {speech_start} to {speech_end}")
            
            speech_tensor = combined[speech_start:speech_end]
            
            # Convert to numpy (float32 in range [-1, 1])
            speech_audio = speech_tensor.numpy()
            print(f"[DEBUG] Audio shape: {speech_audio.shape}, duration: {len(speech_audio) / 16000:.2f}s")
            
            if len(speech_audio) > 0:
                # Transcribe with faster-whisper
                segments, info = whisper_model.transcribe(speech_audio, language="en")
                segments_list = list(segments)
                
                text = "".join([segment.text for segment in segments_list]).strip()
                print(f"[DEBUG] Segments: {len(segments_list)}, Text: '{text}'")
                if text:
                    print(f"Transcribed text: {text}")
                
                # Reset buffer after successful transcription
                audio_buffer = []
            else:
                print("[DEBUG] Empty speech segment, skipping transcription")

        # Optional: trim buffer to avoid unlimited growth
        if len(audio_buffer) > 50:
            audio_buffer = audio_buffer[-10:]

except KeyboardInterrupt:
    process.terminate()