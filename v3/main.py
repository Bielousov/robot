import os, sys, time

# Add the 'lib' directory to sys.path to ensurethat libs can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import ENV, OPEN_AI
from threads import ChatThread, EyesThread
from lib.Audio import Audio
from lib.Eyes import Eyes
from lib.OpenAiClient import OpenAiClient
from lib.Threads import Threads

audio = Audio()
eyes = Eyes()
chatGPT = OpenAiClient(OPEN_AI.MODEL, OPEN_AI.MODEL_TTS, OPEN_AI.PERSONALITY, OPEN_AI.VOICE, audio)
threads = Threads()

def start():
    threads.start(ChatThread(chatGPT))
    threads.start(EyesThread(eyes))

    eyes.open()
    chatGPT.setPrompt('Hello. Tell me about yourself.')
    eyes.blink()
    time.sleep(5)
    chatGPT.setPrompt("What's new?")

def shutdown():
    print("Fine, you killed " .ENV.NAME, ", hope you are happy!")
    eyes.clear()
    audio.clear()
    time.sleep(0.5)
    threads.stop()
