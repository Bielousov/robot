import subprocess
from .Threads import Process

class Voice:
    def __init__(self, voice):
        self.__process = Process()
        self.voice = voice
        self.voice.set_float("duration_stretch", 0.9) 

    def say(self, text):
        # Build the Flite command
        command = [
            "flite",
            "-t", text, 
            "-voice", self.voice,
        ]
        
        # Execute the command
        try:
            subprocess.run(command, check=True)
    
        except subprocess.CalledProcessError as e:
            print("Error while running Flite:", e)

    def sayAsync(self, text):
        self.__process.run(self._say, text)