import os, sys, time

# Add the 'lib' directory to sys.path to ensurethat libs can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import ENV, OPEN_AI
from threads import ChatThread, EyesThread, VoiceThread
from lib.Audio import Audio
from lib.Eyes import Eyes
from lib.OpenAiClient import OpenAiClient
from lib.Threads import Threads

eyes = Eyes()
voice = Audio(
    bufferSize = ENV.VOICE_FRAMES_PER_BUFFER,
    sampleRate = ENV.VOICE_SAMPLE_RATE,
)
chatGPT = OpenAiClient(
    config = OPEN_AI, 
    audio = voice, 
)

threads = Threads()

def start():
    threads.start(ChatThread(chatGPT))
    threads.start(EyesThread(eyes))
    threads.start(VoiceThread(voice))

    eyes.open()
    chatGPT.setPrompt('Hello. Tell me about yourself.')

def shutdown():
    chatGPT.setPrompt("Get ready to die! Say goodbyes and your catch phrase before being turned off.")
    chatGPT.runQuery()
    time.sleep(5)
    print(f"Fine, you killed {ENV.NAME}, hope you are happy!")
    eyes.clear()
    voice.clear()
    threads.stop()

