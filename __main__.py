import os, signal, sys

# Add the 'lib' directory to sys.path to ensure Lib1 and Lib2 can be imported in both v1 and v2 scripts
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))

# Set the path for the v2 directory (ensure that v2/main.py can be run)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'v2'))
# sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'v3'))

import v2.main

def exitSignal(signal, frame):
    print("Handling exit signal:", signal)
    v2.main.shutdown()
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, exitSignal)
    signal.signal(signal.SIGTERM, exitSignal)

    # Run the entry point of v2 main.py when the root-level main.py is executed
    v2.main.start()  # Assuming v2/main.py has a `run()` function or the desired entry point