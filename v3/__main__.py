import signal, sys
import main

def exitSignal(signal, frame):
    print("Handling exit signal:", signal)
    main.shutdown()
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, exitSignal)
    signal.signal(signal.SIGTERM, exitSignal)

    # Run the entry point of v2 main.py when the root-level main.py is executed
    main.start()  # Assuming v2/main.py has a `run()` function or the desired entry point