import json
import subprocess
import sys
from pathlib import Path

# Anchor to project root (v4)
# __file__ is v4/tests/brain/main.py
# .parent.parent.parent is /home/pip/projects/robot/v4/
v4_path = Path(__file__).parent.parent.parent.resolve()

if str(v4_path) not in sys.path:
    sys.path.insert(0, str(v4_path))

from config import Env

LIB_VOSK_DIR = v4_path / "lib" / "vosk"
MODEL_PATH = LIB_VOSK_DIR / "models" / Env.VoskModel
DIST_PATH = LIB_VOSK_DIR / "dist" / "vosk"
SAMPLE_RATE = Env.VoskSampleRate

from vosk import Model, KaldiRecognizer

model = Model(str(MODEL_PATH))
rec = KaldiRecognizer(model, SAMPLE_RATE)

print("[VOSK] Listening... (Ctrl+C to stop)")

# Start arecord process
try:
    process = subprocess.Popen(
        [
            "arecord",
            "-f", "S16_LE",
            "-r", str(SAMPLE_RATE),
            "-c", "1",
            "-t", "raw"
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
except FileNotFoundError:
    print("[ERROR] arecord not found. Install alsa-utils: apt install alsa-utils")
    sys.exit(1)

while True:
    data = process.stdout.read(4000)
    if len(data) == 0:
        break

    if rec.AcceptWaveform(data):
        result = json.loads(rec.Result())
        text = result.get("text", "")
        if text:
            print(">>>", text)
