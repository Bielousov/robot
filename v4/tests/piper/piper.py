import subprocess
from pathlib import Path

# 1. Setup paths relative to this test script
BASE_PATH = Path(__file__).parent.absolute()
PIPER_BIN = BASE_PATH / "piper" / "piper"
MODEL_PATH = BASE_PATH / "piper" / "voices" / "en_US-lessac-medium.onnx"

def test_speech(text):
    print(f"--- Piper Diagnostic ---")
    print(f"Binary: {PIPER_BIN} ({'Found' if PIPER_BIN.exists() else 'MISSING'})")
    print(f"Model:  {MODEL_PATH} ({'Found' if MODEL_PATH.exists() else 'MISSING'})")
    print(f"Testing text: '{text}'")
    
    # The shell command used in your Voice.py
    command = (
        f'echo "{text}" | '
        f'"{PIPER_BIN}" --model "{MODEL_PATH}" --output_raw | '
        f'aplay -r 22050 -f S16_LE -t raw'
    )

    try:
        # We use run() here instead of Popen() so the script waits 
        # for the speech to finish before closing.
        subprocess.run(command, shell=True, check=True)
        print("--- Test Complete ---")
    except subprocess.CalledProcessError as e:
        print(f"Error: Command failed. {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    test_phrase = "Hello. This is a diagnostic test of the Piper text to speech engine on my Raspberry Pi 5."
    test_speech(test_phrase)