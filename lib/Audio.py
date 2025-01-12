from pyaudio import PyAudio, paInt16

class Audio:
    def __init__(self, bufferSize, sampleRate):
        self.audio = PyAudio()
        self.channels=1
        self.format=paInt16
        self.frames_per_buffer=bufferSize
        self.sample_rate=sampleRate

        self.__stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            output=True,
            rate=self.sample_rate,
            frames_per_buffer=self.frames_per_buffer
        )
    
    def output(self, audioData):
        if not audioData:
            return
    
        self.__stream.write(audioData)


    def clear(self):
        self.__stream.stop_stream()
        self.__stream.close()
        self.audio.terminate()
