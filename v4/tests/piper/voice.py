import subprocess, sys
from pathlib import Path

# Anchor to project root (v4)
# __file__ is v4/tests/brain/main.py
# .parent.parent.parent is /home/pip/projects/robot/v4/
v4_path = Path(__file__).parent.parent.parent.resolve()

if str(v4_path) not in sys.path:
    sys.path.insert(0, str(v4_path))

from lib.Voice import Voice

from config import ENV

def test_speech(text):
    print(f"--- Piper Diagnostic ---")
    print(f"Project Root: {v4_path}")
    print(f"Voice Model: {ENV.VOICE}")

    voice = Voice(ENV.VOICE)

    # Escape quotes for shell safety
    clean_text = text.replace('"', '\\"')

    try:
        voice.say(clean_text)
        print("--- Test Complete ---")
    except subprocess.CalledProcessError as e:
        print(f"Error: Playback failed. {e}")

if __name__ == "__main__":
    test_phrase = "Diagnostic test: The robot's voice is now correctly mapped to the library folder."
    test_speech(test_phrase)