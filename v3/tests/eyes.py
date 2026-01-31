import os
import random
import signal
import sys
import time
import threading

# Set the path for the v3 directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from v3.lib.Eyes import Eyes
from v3.lib.Threads import Threads
from v3.threads import EyesThread

eyes = Eyes()
threads = Threads()

# Event to stop all threads
stop_event = threading.Event()

def periodic_blink():
    while not stop_event.is_set():
        print("Blink")
        eyes.blink()  # generate multiple frames for smooth blink
        time.sleep(random.uniform(1, 8))


def periodic_wonder():
    while not stop_event.is_set():
        print("Wonder")
        eyes.wonder()  # generate multiple frames for smooth movement
        time.sleep(random.uniform(5, 10))


def start():
    print("Starting eyes test…")

    threads.start(EyesThread(eyes, threads))
    
    # Open eyes after a short delay
    time.sleep(1)
    eyes.open()


def _graceful_shutdown(signum, frame):
    print("Shutting down…")
    stop_event.set()

    time.sleep(.5)
    eyes.close()
    time.sleep(.5)


def main():
    # Register signals
    signal.signal(signal.SIGINT, _graceful_shutdown)
    signal.signal(signal.SIGTERM, _graceful_shutdown)

    # Start periodic blink and wonder threads
    blink_thread = threading.Thread(target=periodic_blink, daemon=True)
    wonder_thread = threading.Thread(target=periodic_wonder, daemon=True)
    blink_thread.start()
    wonder_thread.start()

    # Open eyes
    start()

    try:
        # Keep main thread alive
        while not stop_event.is_set():
            time.sleep(0.5)
    except KeyboardInterrupt:
        _graceful_shutdown(None, None)
    finally:
        stop_event.set()
        blink_thread.join(1)
        wonder_thread.join(1)
        threads.stop()
        time.sleep(1)
        sys.exit(0)


if __name__ == "__main__":
    main()
