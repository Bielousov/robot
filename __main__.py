import os, signal, sys

# Add the 'lib' directory to sys.path to ensure Lib1 and Lib2 can be imported in both v1 and v2 scripts
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))

# Set the path for the v3 directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'v3'))

import v3.main

def exitSignal(signal, frame):
    print("Handling exit signal:", signal)
    try:
        v3.main.shutdown()
        sys.exit(0)
    except SystemExit as e:
        print(f"Exiting program with status: {e.code}")

if __name__ == "__main__":
    signal.signal(signal.SIGINT, exitSignal)
    signal.signal(signal.SIGTERM, exitSignal)

    # Run the entry point of v2 main.py when the root-level main.py is executed
    v3.main.start()  # Assuming v2/main.py has a `run()` function or the desired entry point