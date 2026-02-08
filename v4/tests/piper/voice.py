import sys, threading, time
from pathlib import Path

# Path Logic
v4_path = Path(__file__).parent.parent.parent.resolve()
if str(v4_path) not in sys.path:
    sys.path.insert(0, str(v4_path))

from lib.Voice import Voice
from config import Env

speech_done = threading.Event()

def on_speech_finished(success, error=None):
    print(f"\n[DEBUG]: Callback fired! Success={success}")
    if error: print(f"[DEBUG]: Error={error}")
    speech_done.set()

def test_speech(text):
    print(f"--- Piper Diagnostic ---")
    print(f"Voice Model: {Env.Voice}")
    
    voice = Voice(Env.Voice, Env.VoiceSampleRate)
    speech_done.clear()

    print(f"Talking: '{text}'")
    voice.say(text, callback=on_speech_finished)

    print("Main thread: Waiting for signal...")
    
    # Use a loop with a small sleep to ensure we aren't just 
    # flying past the wait due to a daemon thread issue
    start_time = time.time()
    while not speech_done.is_set():
        time.sleep(0.1)
        if time.time() - start_time > 15: # 15 second safety timeout
            print("Main thread: Timed out waiting for Piper!")
            break

    print("--- Test Complete ---")

if __name__ == "__main__":
    test_phrase = "Testing wait logic."
    test_speech(test_phrase)