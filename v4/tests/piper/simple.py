import subprocess, sys
from pathlib import Path

# Anchor to project root (v4)
# __file__ is v4/tests/brain/main.py
# .parent.parent.parent is /home/pip/projects/robot/v4/
v4_path = Path(__file__).parent.parent.parent.resolve()

if str(v4_path) not in sys.path:
    sys.path.insert(0, str(v4_path))

from config import Env

# 3. Define the actual assets location
LIB_PIPER_DIR = v4_path / "lib" / "piper" / "dist"
PIPER_BIN = LIB_PIPER_DIR / "piper"

VOICE_FILE = f"{Env.Voice}.onnx" if Env.Voice else "en_US-danny-low.onnx"
VOICE_SAMPLE_RATE = Env.VoiceSampleRate or 16_000
MODEL_PATH = LIB_PIPER_DIR / "voices" / VOICE_FILE

def test_speech(text):
    print(f"--- Piper Diagnostic ---")
    print(f"Project Root: {v4_path}")
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
        f'aplay -r {VOICE_SAMPLE_RATE} -f S16_LE -t raw'
    )

    try:
        subprocess.run(command, shell=True, check=True)
        print("--- Test Complete ---")
    except subprocess.CalledProcessError as e:
        print(f"Error: Playback failed. {e}")

if __name__ == "__main__":
    test_phrase = "Diagnostic test: The robot's voice is now correctly mapped to the library folder."
    test_speech(test_phrase)