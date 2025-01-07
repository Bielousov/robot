import os, sys, time

# Add the 'lib' directory to sys.path to ensurethat libs can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import ENV, OPEN_AI
from dictionary import Prompts
from intents import IntentHandler
from threads import ChatThread, EyesThread, IntentThread, VoiceThread
from lib.Eyes import Eyes
from lib.OpenAiClient import OpenAiClient
from lib.Threads import Threads
from lib.Voice import Voice

eyes = Eyes()
openAi = OpenAiClient(config = OPEN_AI)
voice = Voice(ENV.VOICE)
intentHandler = IntentHandler(eyes, openAi, voice)
threads = Threads()

def start():
    threads.start(IntentThread(intentHandler))
    threads.start(EyesThread(eyes))
    threads.start(VoiceThread(voice))

    eyes.open()
    chatGPT.setPrompt(Prompts['startup'])

def shutdown():
    chatGPT.setPrompt(Prompts['shutdown'])
    chatGPT.runQuery()
    time.sleep(5)
    print(f"Fine, you killed {ENV.NAME}, hope you are happy!")
    eyes.clear()
    voice.clear()
    threads.stop()

