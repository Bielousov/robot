import subprocess, sys, threading
from pathlib import Path

# Path Logic
v4_path = Path(__file__).parent.parent.parent.resolve()
if str(v4_path) not in sys.path:
    sys.path.insert(0, str(v4_path))

from lib.Voice import Voice
from config import ENV

# 1. Global event
speech_done = threading.Event()

def on_speech_finished(success, error=None):
    if success:
        print("\n[Callback]: Speech finished successfully!")
    else:
        # Check if error is None to avoid formatting issues
        err_msg = error if error else "Unknown Error (Check Piper paths)"
        print(f"\n[Callback]: Speech failed: {err_msg}")
    
    # 3. Turn light green
    speech_done.set()

def test_speech(text):
    print(f"--- Piper Diagnostic ---")
    print(f"Voice Model: {ENV.VOICE}")

    voice = Voice(ENV.VOICE)

    # 2. IMPORTANT: Reset the light to RED before starting
    speech_done.clear()

    print(f"Talking: '{text}'")
    voice.say(text, callback=on_speech_finished)

    print("Main thread: Blocking now, waiting for callback signal...")
    
    # Wait here. If it still doesn't wait, Piper is likely exiting 
    # so fast that you can't see the delay.
    speech_done.wait() 
    
    print("Main thread: Signal received. --- Test Complete ---")

if __name__ == "__main__":
    test_phrase = "Diagnostic test: The robot's voice is now correctly mapped."
    test_speech(test_phrase)