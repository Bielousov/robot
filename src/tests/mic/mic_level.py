import sounddevice as sd
import numpy as np

RATE = 16000
BLOCK = 1024

def callback(indata, frames, time, status):
    if status:
        print(status)

    rms = np.sqrt(np.mean(indata**2))
    db = 20 * np.log10(max(rms, 1e-10))

    bars = int(max(0, min(50, (db + 60) / 60 * 50)))
    print(f"\rMic: {db:6.1f} dB | {'█' * bars:<50}", end="", flush=True)

with sd.InputStream(
    samplerate=RATE,
    channels=1,
    dtype="float32",
    blocksize=BLOCK,
    callback=callback,
):
    print("Speak into the microphone. Ctrl+C to stop.")
    while True:
        sd.sleep(1000)