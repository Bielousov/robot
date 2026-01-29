import os
import random
import signal
import sys
import time
import threading

# Set the path for the v3 directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../v3"))

from v3.config import ENV
from v3.lib.Voice import Voice

voice = Voice(ENV.VOICE)

# Event to stop all threads
stop_event = threading.Event()

def periodic_say():
    while not stop_event.is_set():
        print("Say")
        voice.say("Test")
        time.sleep(random.uniform(5, 10))

def start():
    print("Starting voice test…")

    voice.say("Hello, this is voice test…")


def _graceful_shutdown(signum, frame):
    print("Shutting down…")
    stop_event.set()
    voice.say("Bye bye then.")


def main():
    # Register signals
    signal.signal(signal.SIGINT, _graceful_shutdown)
    signal.signal(signal.SIGTERM, _graceful_shutdown)

    # Start periodic saying threads
    say_thread = threading.Thread(target=periodic_say, daemon=True)
    say_thread.start()

    start()

    try:
        # Keep main thread alive
        while not stop_event.is_set():
            time.sleep(0.5)
    except KeyboardInterrupt:
        _graceful_shutdown(None, None)
    finally:
        stop_event.set()
        say_thread.join(1)
        time.sleep(1)
        sys.exit(0)


if __name__ == "__main__":
    main()
