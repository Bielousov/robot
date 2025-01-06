from time import sleep
from pyaudio import PyAudio, paInt8

class Audio:
    def __init__(self):
        self.audio = PyAudio()
        self.channels=1
        self.format=paInt8
        self.latency=0.1
        self.sample_rate=24_000
        self.stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.sample_rate,
            output=True,
            output_latency=self.latency
        )
    def output(self, audio):
        self.stream.write(audio)