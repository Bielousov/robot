import subprocess
import os
from pathlib import Path

# --- Path Resolution ---
# 1. Get the directory where THIS test script lives
# Path(__file__) = /home/pip/projects/robot/v4/tests/piper/piper.py
THIS_DIR = Path(__file__).parent.resolve()

# 2. Navigate to the project root (v4)
# We go up 2 levels: piper/ -> tests/ -> v4/
V4_ROOT = THIS_DIR.parent.parent

# 3. Define the actual assets location
LIB_PIPER_DIR = V4_ROOT / "lib" / "piper"
PIPER_BIN = LIB_PIPER_DIR / "piper"
MODEL_PATH = LIB_PIPER_DIR / "voices" / "en_US-lessac-medium.onnx"

def test_speech(text):
    print(f"--- Piper Diagnostic ---")
    print(f"Project Root: {V4_ROOT}")
    print(f"Binary:       {PIPER_BIN} ({'Found' if PIPER_BIN.exists() else 'MISSING'})")
    print(f"Model:        {MODEL_PATH} ({'Found' if MODEL_PATH.exists() else 'MISSING'})")
    
    if not PIPER_BIN.exists():
        print(f"\n[!] ERROR: Ensure Piper is installed in {LIB_PIPER_DIR}")
        return

    # Escape quotes for shell safety
    clean_text = text.replace('"', '\\"')
    
    command = (
        f'echo "{clean_text}" | '
        f'"{PIPER_BIN}" --model "{MODEL_PATH}" --output_raw | '
        f'aplay -r 22050 -f S16_LE -t raw'
    )

    try:
        subprocess.run(command, shell=True, check=True)
        print("--- Test Complete ---")
    except subprocess.CalledProcessError as e:
        print(f"Error: Playback failed. {e}")

if __name__ == "__main__":
    test_phrase = "Diagnostic test: The robot's voice is now correctly mapped to the library folder."
    test_speech(test_phrase)