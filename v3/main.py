import os, sys, time

# Add the 'lib' directory to sys.path to ensurethat libs can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from v3.lib.Eyes import Eyes
from v3.lib.IntentsModel import IntentsModel
from v3.lib.OpenAiClient import OpenAiClient
from v3.lib.Threads import Threads
from v3.lib.Voice import Voice

from config import ENV, MODEL, OPEN_AI
from dictionary import Prompts
from intents import IntentHandler
from state import State
from threads import EyesThread, IntentsThread

eyes = Eyes()
openAi = OpenAiClient(OPEN_AI)
voice = Voice(ENV.VOICE)
intentsModel = IntentsModel(MODEL)
intentHandler = IntentHandler(eyes, intentsModel, openAi, voice)

threads = Threads()

def start():
    threads.start(IntentsThread(intentsModel, intentHandler, threads))
    threads.start(EyesThread(eyes, threads))

def shutdown():
    State.set('on', False)
    time.sleep(5)
    threads.stop()
    time.sleep(1)
    print(f"Fine, you killed {ENV.NAME}, hope you are happy!")