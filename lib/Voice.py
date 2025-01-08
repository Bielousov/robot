import subprocess, time
from Threads import Process

class Voice:
    def __init__(self, voice):
        self._process = None
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

        finally:
            self._process.stop()

        
    def say(self, text):
        self._process = Process(self._say, (text))
