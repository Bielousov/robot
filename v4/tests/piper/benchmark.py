import os, subprocess, sys, time
from pathlib import Path

# Anchor to project root (v4)
# __file__ is v4/tests/brain/main.py
# .parent.parent.parent is /home/pip/projects/robot/v4/
v4_path = Path(__file__).parent.parent.parent.resolve()

if str(v4_path) not in sys.path:
    sys.path.insert(0, str(v4_path))

# Configuration - Update these to your actual paths
LIB_PIPER_DIR = v4_path / "lib" / "piper"
PIPER_BIN = LIB_PIPER_DIR / "piper"

VOICE = "en_US-danny-low"
VOICE_FILE = f"{VOICE}.onnx"
VOICE_SAMPLE_RATE = 16_000
MODEL_PATH = LIB_PIPER_DIR / "voices" / VOICE_FILE

TEST_PHRASE = "The quick brown fox jumps over the lazy dog."

def run_benchmark(threads=2, niceness=10):
    print(f"\n--- Testing: Threads={threads}, Nice={niceness} ---")
    
    # Using 'time' utility to measure system resources and the optimized command
    # We pipe to /dev/null for the benchmark to ignore speaker latency
    command = (
        f'echo "{TEST_PHRASE}" | '
        f'nice -n {niceness} "{PIPER_BIN}" --model "{MODEL_PATH}" '
        f'--threads {threads} --output_raw > /dev/null'
    )

    command = (
        f'echo "{TEST_PHRASE}" | '
        f'nice -n {niceness} "{PIPER_BIN}" '
        f'--model "{MODEL_PATH}" '
        f'--threads {threads} '
        f'--output_raw | '
        f'aplay -r {VOICE_SAMPLE_RATE} -f S16_LE -t raw'
    )

    start_time = time.perf_counter()
    
    process = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    end_time = time.perf_counter()
    duration = end_time - start_time

    if process.returncode == 0:
        print(f"Total Execution Time: {duration:.4f} seconds")
        # Estimate: average speaking speed is ~150 words per minute
        # Phrase has 9 words -> approx 3.6 seconds of audio
        est_audio_len = 3.6 
        rtf = duration / est_audio_len
        print(f"Estimated Real-Time Factor (RTF): {rtf:.2f}")
        if rtf < 1:
            print("Status: EXCELLENT (Faster than real-time)")
        else:
            print("Status: WARNING (May cause audio stuttering)")
    else:
        print(f"Error: {process.stderr}")

if __name__ == "__main__":
    if not os.path.exists(MODEL_PATH):
        print(f"Error: Model not found at {MODEL_PATH}")
    else:
        # Compare 1 thread vs 2 threads
        run_benchmark(threads=1)
        run_benchmark(threads=2)
        run_benchmark(threads=3)
        run_benchmark(threads=4)