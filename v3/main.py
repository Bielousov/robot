import os, sys, time

# Add the 'lib' directory to sys.path to ensurethat libs can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lib.Eyes import Eyes
from lib.IntentsModel import IntentsModel
from lib.OpenAiClient import OpenAiClient
from lib.Threads import Threads
from lib.Voice import Voice

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
    threads.start(IntentsThread(intentsModel, intentHandler))
    threads.start(EyesThread(eyes))
    State.append('prompts', Prompts['startup'])

def shutdown():
    State.append('prompts', Prompts['shutdown'])
    time.sleep(5)
    threads.stop()
    print(f"Fine, you killed {ENV.NAME}, hope you are happy!")