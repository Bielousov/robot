import signal, sys, time
import main

def exitSignal(signal, frame):
    print("Handling exit signal:", signal)
    
    try:
        main.shutdown()
        time.sleep(.5)
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

    # Run the entry point of v4 main.py when the root-level main.py is executed
    main.start()  # Assuming v4/main.py has a `run()` function or the desired entry point