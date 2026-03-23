import subprocess
import sys
import io
import tempfile
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

# Verify model and binary exist
if not WHISPER_BIN.exists():
    print(f"[ERROR] Whisper binary not found at {WHISPER_BIN}")
    print("[INFO] Run: bash src/lib/whisper/install.sh")
    sys.exit(1)

if not MODEL_PATH.exists():
    print(f"[ERROR] Model not found at {MODEL_PATH}")
    print("[INFO] Run: bash src/lib/whisper/install.sh")
    sys.exit(1)

RECORD_DURATION = 5  # seconds

print(f"[WHISPER] Listening for {RECORD_DURATION} seconds... (Ctrl+C to stop)")
print(f"[CONFIG] Model: {Env.WhisperModel}")
print(f"[CONFIG] Sample Rate: {SAMPLE_RATE}")

# Create a buffer for audio data (stays in RAM)
audio_buffer = io.BytesIO()

try:
    # 1. Record audio to buffer with arecord
    print(f"[RECORD] Capturing audio to memory buffer...")
    record_cmd = [
        "arecord",
        "-f", "S16_LE",
        "-r", str(SAMPLE_RATE),
        "-c", "1",
        "-d", str(RECORD_DURATION),
        "-t", "wav"
    ]
    
    try:
        # Use PIPE to capture output, then write to buffer
        result = subprocess.run(record_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        audio_buffer.write(result.stdout)
        audio_buffer.seek(0)
    except FileNotFoundError:
        print("[ERROR] arecord not found. Install alsa-utils: apt install alsa-utils")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Recording failed: {e.stderr.decode() if e.stderr else e}")
        sys.exit(1)
    
    # 2. Write buffer to temporary file for whisper.cpp (stays in RAM until size limit)
    # SpooledTemporaryFile keeps data in memory up to max_size, then spills to disk
    with tempfile.SpooledTemporaryFile(max_size=5*1024*1024, suffix=".wav") as tmp:
        tmp.write(audio_buffer.getvalue())
        tmp.flush()
        tmp.seek(0)
        
        # Write to a temporary named file that whisper.cpp can access
        # (spooled file may not have a real path, so we need a named file)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as named_tmp:
            named_tmp.write(tmp.getvalue())
            named_tmp.flush()
            
            # 3. Run whisper.cpp on the buffered audio
            print("[TRANSCRIBE] Running whisper.cpp...")
            whisper_cmd = [
                str(WHISPER_BIN),
                "-m", str(MODEL_PATH),
                "-f", named_tmp.name,
                "--no-prints",
                "-t", "1"  # single thread for consistency
            ]
            
            result = subprocess.run(whisper_cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"[ERROR] Whisper failed: {result.stderr}")
                sys.exit(1)
            
            # 4. Display results
            output = result.stdout.strip()
            if output:
                print("\n[RESULT]")
                print(output)
            else:
                print("[RESULT] No speech detected")

except KeyboardInterrupt:
    print("\n[STOPPED]")
except Exception as e:
    print(f"[ERROR] {e}")

