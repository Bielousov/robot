
import random
import sys
import time
from pathlib import Path

# Anchor to project root (src) so `config` and `lib` resolve like other tests.
PROJECT_PATH = Path(__file__).parent.parent.parent.resolve()
if str(PROJECT_PATH) not in sys.path:
    sys.path.insert(0, str(PROJECT_PATH))

from lib.Eyes import Eyes
from lib.Threads import Thread, Threads

INTERVAL = 1 / 30 #FPS
SPI_DEV_PORT = 10
SPI_DEV_DEVICE=0

def main():
    try:
        eyes = Eyes(port = SPI_DEV_PORT, device = SPI_DEV_DEVICE)

        def runThread():
            print("running eyes thread")
            if random.triangular(0, 1, 0) > 0.99:
                eyes.wonder()
            elif random.triangular(0, 1, 0) > 0.95:
                eyes.blink()
            eyes.render()
        
        threads = Threads()
        eyesThread = threads.start(INTERVAL, runThread)

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n[Eyes] Stopping...")
        eyesThread.stop()

if __name__ == "__main__":
    main()