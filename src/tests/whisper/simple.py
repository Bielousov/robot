import subprocess
import sys
import io
import struct
from pathlib import Path

# Anchor to project root (src)
# __file__ is src/tests/whisper/simple.py
# .parent.parent.parent is /home/pip/projects/robot/src/
project_path = Path(__file__).parent.parent.parent.resolve()

if str(project_path) not in sys.path:
    sys.path.insert(0, str(project_path))

from config import Env

LIB_WHISPER_DIR = project_path / "lib" / "whisper"
MODEL_PATH = LIB_WHISPER_DIR / "models" / f"{Env.WhisperModel}.bin"
WHISPER_BIN = LIB_WHISPER_DIR / "dist" / "build" / "bin" / "whisper-cli"

SAMPLE_RATE = Env.WhisperSampleRate
CHUNK_SIZE = 4096  # bytes per chunk (~256ms at 16kHz, 16-bit mono)
SILENCE_THRESHOLD = 500  # amplitude threshold for silence detection
SILENCE_DURATION = 2.0  # seconds of silence to trigger stop
SILENCE_CHUNKS = int(SILENCE_DURATION * SAMPLE_RATE * 2 / CHUNK_SIZE)  # 2 sec worth of chunks

# Verify model and binary exist
if not WHISPER_BIN.exists():
    print(f"[ERROR] Whisper binary not found at {WHISPER_BIN}")
    print("[INFO] Run: bash src/lib/whisper/install.sh")
    sys.exit(1)

if not MODEL_PATH.exists():
    print(f"[ERROR] Model not found at {MODEL_PATH}")
    print("[INFO] Run: bash src/lib/whisper/install.sh")
    sys.exit(1)

print(f"[WHISPER] Listening for speech (continuous mode)... (Ctrl+C to stop)")
print(f"[CONFIG] Model: {Env.WhisperModel}")
print(f"[CONFIG] Sample Rate: {SAMPLE_RATE}")

def is_silence(chunk, threshold=SILENCE_THRESHOLD):
    """Check if audio chunk is silent (low amplitude)"""
    if len(chunk) < 2:
        return True
    try:
        # Unpack as 16-bit signed integers
        samples = struct.unpack(f'<{len(chunk)//2}h', chunk)
        # Calculate RMS (root mean square) amplitude
        rms = (sum(s**2 for s in samples) / len(samples)) ** 0.5
        return rms < threshold
    except:
        return False

try:
    # Start recording process continuously
    print(f"[RECORD] Capturing audio (waiting for speech)...")
    record_cmd = [
        "arecord",
        "-f", "S16_LE",
        "-r", str(SAMPLE_RATE),
        "-c", "1",
        "-t", "raw"
    ]
    
    try:
        process = subprocess.Popen(record_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        print("[ERROR] arecord not found. Install alsa-utils: apt install alsa-utils")
        sys.exit(1)
    
    utterance_num = 0
    
    while True:
        # Reset buffer for each utterance
        audio_buffer = io.BytesIO()
        silent_chunk_count = 0
        audio_started = False
        utterance_num += 1
        
        # Record until silence is detected
        while True:
            chunk = process.stdout.read(CHUNK_SIZE)
            if not chunk:
                break
            
            audio_buffer.write(chunk)
            
            # Detect silence
            if is_silence(chunk):
                if audio_started:
                    silent_chunk_count += 1
                    if silent_chunk_count % 5 == 0:
                        print(f"[SILENCE] {silent_chunk_count}/{SILENCE_CHUNKS} chunks", end='\r')
                    
                    # Chunk the audio when silence is detected
                    if silent_chunk_count >= SILENCE_CHUNKS:
                        print(f"\n[CHUNK] Utterance #{utterance_num} complete")
                        break
            else:
                if not audio_started:
                    print(f"[SPEECH] Speech detected, recording utterance #{utterance_num}...")
                    audio_started = True
                silent_chunk_count = 0
        
        # Only process if we captured speech
        if audio_started and audio_buffer.tell() > 0:
            # Reset buffer position
            audio_buffer.seek(0)
            
            # Transcribe this chunk
            print(f"[TRANSCRIBE] Processing utterance #{utterance_num}...")
            whisper_cmd = [
                str(WHISPER_BIN),
                "-m", str(MODEL_PATH),
                "-f", "/dev/stdin",
                "--no-prints",
                "-t", "1"  # single thread for consistency
            ]
            
            try:
                result = subprocess.run(
                    whisper_cmd,
                    input=audio_buffer.getvalue(),
                    capture_output=True,
                    timeout=30
                )
                
                if result.returncode != 0:
                    print(f"[ERROR] Whisper failed: {result.stderr.decode()}")
                else:
                    # Display results
                    output = result.stdout.decode().strip()
                    if output:
                        print(f"[RESULT #{utterance_num}]")
                        print(output)
                    else:
                        print(f"[RESULT #{utterance_num}] No speech detected")
            
            except subprocess.TimeoutExpired:
                print(f"[ERROR] Whisper transcription timed out for utterance #{utterance_num}")
        
        print()  # Blank line for readability

except KeyboardInterrupt:
    print("\n[STOPPED] Terminating recording...")
    try:
        process.terminate()
        process.wait(timeout=2)
    except:
        process.kill()
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
    try:
        process.kill()
    except:
        pass


