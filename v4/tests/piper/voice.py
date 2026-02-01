import subprocess, sys, threading
from pathlib import Path

# Anchor to project root (v4)
# __file__ is v4/tests/brain/main.py
# .parent.parent.parent is /home/pip/projects/robot/v4/
v4_path = Path(__file__).parent.parent.parent.resolve()

if str(v4_path) not in sys.path:
    sys.path.insert(0, str(v4_path))

from lib.Voice import Voice

from config import ENV

# 1. Create a "Stoplight" event
speech_done = threading.Event()

def on_speech_finished(success, error=None):
    if success:
        print("\n[Callback]: Speech finished successfully!")
    else:
        print(f"\n[Callback]: Speech failed: {error}")
    
    # Signal the main thread to continue
    speech_done.set()

def test_speech(text):
    print(f"--- Piper Diagnostic ---")
    print(f"Project Root: {v4_path}")
    print(f"Voice Model: {ENV.VOICE}")

    voice = Voice(ENV.VOICE)

    try:
        print(f"Talking: '{text}'")

        voice.say(text, callback=on_speech_finished)

        print("Main thread is waiting for callback...")
        speech_done.wait() 
        print("--- Test Complete ---")
    except subprocess.CalledProcessError as e:
        print(f"Error: Playback failed. {e}")

if __name__ == "__main__":
    test_phrase = "Diagnostic test: The robot's voice is now correctly mapped to the library folder."
    test_speech(test_phrase)