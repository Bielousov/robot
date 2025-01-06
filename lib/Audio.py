from time import sleep
from pyaudio import PyAudio

class Audio:
    def __init__(self):
        self.audio = PyAudio()
        self.stream = self.audio.open(
            format=8,
            channels=1,
            rate=24_000,
            output=True
        )
    def output(self, audio):
        self.stream.write(audio)