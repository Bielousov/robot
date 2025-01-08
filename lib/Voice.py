import subprocess, time
from threading import Thread

class Voice:
    def __init__(self, voice):
        self.text_to_say = None
        self.thread = Thread(target=self._thread_target)
        self.thread.daemon = True  # Daemonize the thread to exit when the main program ends
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

    def _thread_target(self):
        # This function runs in the background thread
        while True:
            if self.text_to_say:
                self._say(self.text_to_say)
                self.text_to_say = None
            else:
                time.sleep(0.1)

    def say(self, text):
        self.text_to_say = text
        if not self.thread.is_alive():
            self.thread.start()