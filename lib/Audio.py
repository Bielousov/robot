from time import sleep
from pyaudio import PyAudio, paContinue, paInt8

class Audio:
    def __init__(self):
        self.audio = PyAudio()
        self.buffer = []
        self.channels=1
        self.format=paInt8
        self.sample_rate=24_000

        self.stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.sample_rate,
            output=True,
            stream_callback=self.audio_callback,
        )

    def audio_callback(self, in_data, frame_count, time_info, status):
        """Non-blocking callback for PyAudio stream."""
        if self.buffer:
            # Pop the first chunk from the queue
            chunk = self.buffer.pop(0)
        else:
            # If no data available, send silence
            chunk = b'\x00' * frame_count * self.channels

        return (chunk, paContinue)


    def output(self, chunk):
        self.buffer.append(chunk)
        

    def start(self):
        self.stream.start_stream()

    def stop(self):
        self.stream.stop_stream()

    def clear(self):
        self.audio.stop()