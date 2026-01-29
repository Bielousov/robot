import os
import random
import signal
import sys
import time
import threading

# Set the path for the v3 directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "v3"))

from v3.lib.Eyes import Eyes

# Create Eyes instance
eyes = Eyes()

# Event to stop all threads
stop_event = threading.Event()

FPS = 30
FRAME_INTERVAL = 1.0 / FPS  # seconds per frame


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


def eyes_render_loop():
    """Render eyes at fixed FPS."""
    while not stop_event.is_set():
        eyes.render()
        time.sleep(FRAME_INTERVAL)


def start():
    print("Starting eyes test…")
    # Open eyes after a short delay
    time.sleep(1)
    eyes.open()


def _graceful_shutdown(signum, frame):
    print("Shutting down…")
    stop_event.set()
    eyes.close()
    time.sleep(1)


def main():
    # Register signals
    signal.signal(signal.SIGINT, _graceful_shutdown)
    signal.signal(signal.SIGTERM, _graceful_shutdown)

    # Start the render thread (30 FPS)
    render_thread = threading.Thread(target=eyes_render_loop, daemon=True)
    render_thread.start()

    # Start periodic blink and wonder threads
    blink_thread = threading.Thread(target=periodic_blink, daemon=True)
    wonder_thread = threading.Thread(target=periodic_wonder, daemon=True)

    blink_thread.start()
    wonder_thread.start()

    # Open eyes
    start()

    # Keep main thread alive
    try:
        while not stop_event.is_set():
            time.sleep(0.5)
    finally:
        stop_event.set()
        render_thread.join(1)
        blink_thread.join(1)
        wonder_thread.join(1)
        sys.exit(0)


if __name__ == "__main__":
    main()
