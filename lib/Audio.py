from pyaudio import PyAudio, paInt16

class Audio:
    def __init__(self, bufferSize, sampleRate):
        self.audio = PyAudio()
        self.audioBuffer=[]
        self.channels=1
        self.format=paInt16
        self.frames_per_buffer=bufferSize
        self.sample_rate=sampleRate

        self.stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            output=True,
            rate=self.sample_rate,
            frames_per_buffer=self.frames_per_buffer
        )
    
    def append(self, chunk):
        self.audioBuffer.append(chunk)

    def output(self):
        if not self.audioBuffer:
            return
    
        self.stream.write(self.audioBuffer.pop(0))


    def clear(self):
        self.audioBuffer=[]
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()
