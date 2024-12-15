import numpy as np, os, sys, time

# Add the 'lib' directory to sys.path to ensurethat libs can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import ENV, OPEN_AI
from threads import EyesThread
from lib.Eyes import Eyes
from lib.OpenAiClient import OpenAiClient
from lib.Threads import Threads

np.set_printoptions(suppress=True)

eyes = Eyes()
chatGPT = OpenAiClient(OPEN_AI.MODEL, OPEN_AI.PERSONALITY)
threads = Threads()

def start():
    eyes.clear()
    threads.start(EyesThread(eyes))

    print(chatGPT.query('Who are you?'))

def shutdown():
    print("Fine, you killed " .ENV.NAME, ", hope you are happy!")
    eyes.clear()
    time.sleep(0.5)
    threads.stop()

