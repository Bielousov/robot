import numpy as np, os, sys, time

# Add the 'lib' directory to sys.path to ensurethat libs can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import ENV
from threads import EyesThread
from lib.Eyes import Eyes
from lib.Threads import Threads

np.set_printoptions(suppress=True)

eyes = Eyes()
threads = Threads()

def run():
    eyes.clear()
    threads.start(EyesThread(eyes))
    print(ENV.NAME, "is here!")

def shutdown():
    print("You killed " .ENV.NAME, ", hope you are happy!")
    eyes.clear()
    time.sleep(0.5)
    threads.stop()

