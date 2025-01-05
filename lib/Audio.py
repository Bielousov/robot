from time import sleep
from pyaudio import PyAudio, paInt16

class Audio:
    def output(self, audioBuffer):
        self.audio = PyAudio()

        # Open a stream with the correct format and sample rate
        self.stream = self.audio.open(
            format=paInt16,
            channels=1,
            rate=16000,  # Ensure this matches the sample rate of the audio
            output=True,
            frames_per_buffer=1024
        )

        chunk = audioBuffer.read(1024)
    
        while audioBuffer:
            self.stream.write(chunk)
            chunk = audioBuffer.read(1024)


         # Close the stream after all data is played
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()
