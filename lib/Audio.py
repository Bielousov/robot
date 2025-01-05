from time import sleep
from pyaudio import PyAudio, paInt16

class Audio:
    def output(self, audioData):
        self.audio = PyAudio()

        # Open a stream with the correct format and sample rate
        self.stream = self.audio.open(
            format=paInt16,
            channels=1,
            rate=16000,  # Ensure this matches the sample rate of the audio
            output=True,
            frames_per_buffer=1024
        )
    
        # Simulate streaming audio data in chunks
        for chunk in audioData:
            # Write data to the output stream in real-time
            self.stream.write(chunk)
            sleep(0.1)  # Sleep for a short time to simulate real-time streaming

         # Close the stream after all data is played
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()
