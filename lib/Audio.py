from pyaudio import PyAudio, paInt16

class Audio:
    def __init__(self):
        self.audio = PyAudio()
        self.channels=1
        self.format=paInt16
        self.frames_per_buffer=1024
        self.sample_rate=24_000

        self.stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            output=True,
            rate=self.sample_rate,
            frames_per_buffer=self.frames_per_buffer
        )

    def output(self, audio):
        self.stream.write(audio)


    def clear(self):
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()