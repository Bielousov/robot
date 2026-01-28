import os, signal, sys

# Set the path for the v3 directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'v3'))

import v3.main

def exitSignal(signal, frame):
    print("Handling exit signal:", signal)
    try:
        v3.main.shutdown()
        sys.exit(0)
    except KeyboardInterrupt:
        print("Keyboard interrupt received. Exiting.")
        sys.exit(1)
    except SystemExit as e:
        print(f"Exiting program with status: {e.code}")
        raise  # Re-raise SystemExit to terminate the program

if __name__ == "__main__":
    signal.signal(signal.SIGINT, exitSignal)
    signal.signal(signal.SIGTERM, exitSignal)

    # Run the entry point of v3 main.py when the root-level main.py is executed
    v3.main.start()  # Assuming v3/main.py has a `run()` function or the desired entry point