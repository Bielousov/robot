import os, sys, time

# Add the 'lib' directory to sys.path to ensurethat libs can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import MODEL, ENV, OPEN_AI
from dictionary import Prompts
from intents import IntentHandler
from state import State
from threads import EyesThread, IntentsThread

from lib.Eyes import Eyes
from lib.IntentsModel import IntentsModel
from lib.OpenAiClient import OpenAiClient
from lib.Threads import Threads
from lib.Voice import Voice

eyes = Eyes()
openAi = OpenAiClient(config = OPEN_AI)
voice = Voice(ENV.VOICE)
intentHandler = IntentHandler(eyes, openAi, voice)
intentsModel = IntentsModel(MODEL)

threads = Threads()

def start():
    threads.start(IntentsThread(intentsModel, intentHandler))
    threads.start(EyesThread(eyes))

    eyes.open();

    State.promptQueue.append(Prompts['startup'])

def shutdown():
    State.promptQueue.append(Prompts['shutdown'])
    time.sleep(5)
    print(f"Fine, you killed {ENV.NAME}, hope you are happy!")
    eyes.clear()
    threads.stop()

