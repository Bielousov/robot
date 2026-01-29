import os, random, signal, sys, time, threading

# Set the path for the v3 directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "v3"))

from v3.lib.Eyes import Eyes
from v3.lib.Threads import Threads
from v3.threads import EyesThread

eyes = Eyes()
threads = Threads()

# Flag to stop periodic functions
stop_event = threading.Event()

def periodic_blink():
    while not stop_event.is_set():
        eyes.blink()
        # Wait a random time between 1 and 8 seconds
        time.sleep(random.uniform(1, 8))

def periodic_wonder():
    while not stop_event.is_set():
        eyes.wonder()
        # Wait a random time between 5 and 10 seconds
        time.sleep(random.uniform(3, 10))

def start():
    print("Starting eyes test…")
    time.sleep(1)
    eyes.open()

def _graceful_shutdown(signum, frame):
    eyes.close()
    time.sleep(1)
    stop_event.set()  # Stop the periodic threads
    threads.stop()

signal.signal(signal.SIGINT, _graceful_shutdown)
signal.signal(signal.SIGTERM, _graceful_shutdown)

def main():
    try:
        # Start the EyesThread
        threads.start(EyesThread(eyes))

        start()

        # Start periodic functions in background threads
        blink_thread = threading.Thread(target=periodic_blink, daemon=True)
        wonder_thread = threading.Thread(target=periodic_wonder, daemon=True)

        blink_thread.start()
        wonder_thread.start()

        # Keep the main thread alive
        while not stop_event.is_set():
            time.sleep(0.5)

    except KeyboardInterrupt:
        _graceful_shutdown(None, None)
    finally:
        sys.exit(0)

if __name__ == "__main__":
    main()