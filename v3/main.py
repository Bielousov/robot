import os, sys,

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
    voice = voice, 
)

threads = Threads()

def start():
    threads.start(ChatThread(chatGPT))
    threads.start(EyesThread(eyes))
    threads.start(VoiceThread(voice))

    eyes.open()
    chatGPT.setPrompt('Hello. Tell me about yourself.')

def shutdown():
    chatGPT.setPrompt("What would be your last words before being killed?")
    chatGPT.runQuery()
    print(f"Fine, you killed {ENV.NAME}, hope you are happy!")
    eyes.clear()
    voice.clear()
    threads.stop()
