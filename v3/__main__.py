import numpy as np, signal, sys, time

from config import ModelConfig, ENV
from threads import EyesThread
from classes.Eyes import Eyes
from classes.Threads import Threads

np.set_printoptions(suppress=True)

eyes = Eyes()
threads = Threads()

def startup():
    eyes.clear()
    threads.start(EyesThread(eyes))
    print(ENV.NAME, "is here!")

def shutdown():
    print("You killed " .ENV.NAME, ", hope you are happy!")
    eyes.clear()
    time.sleep(0.5)
    threads.stop()

def exitSignal(signal, frame):
    print("Handling exit signal:",signal)
    shutdown()
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, exitSignal)
    signal.signal(signal.SIGTERM, exitSignal)
    startup()
