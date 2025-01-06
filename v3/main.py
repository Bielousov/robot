import os, sys, time

# Add the 'lib' directory to sys.path to ensurethat libs can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import ENV, OPEN_AI
from state import voiceBuffer
from threads import ChatThread, EyesThread, VoiceThread
from lib.Audio import Audio
from lib.Eyes import Eyes
from lib.OpenAiClient import OpenAiClient
from lib.Threads import Threads

eyes = Eyes()
chatGPT = OpenAiClient(
    config = OPEN_AI, 
    voiceBuffer = voiceBuffer, 
    voiceBufferSize = ENV.VOICE_FRAMES_PER_BUFFER,
)
voice = Audio(
    bufferSize = ENV.VOICE_FRAMES_PER_BUFFER,
    sampleRate = ENV.VOICE_SAMPLE_RATE,
)
threads = Threads()

def start():
    threads.start(ChatThread(chatGPT))
    threads.start(EyesThread(eyes))
    threads.start(VoiceThread(voice))

    eyes.open()
    chatGPT.setPrompt('Hello. Tell me about yourself.')
    eyes.blink()
    time.sleep(5)
    chatGPT.setPrompt("What's new?")

def shutdown():
    chatGPT.setPrompt("What would be your last words before being killed?")
    print(f"Fine, you killed {ENV.NAME}, hope you are happy!")
    eyes.clear()
    voice.clear()
    time.sleep(5)
    threads.stop()
