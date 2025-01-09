import subprocess, time
from Threads import Process

class Voice:
    def __init__(self, voice):
        self.voice = voice

    def _say(self, text):
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

    def say(self, text):
        Process(self._say, (text))