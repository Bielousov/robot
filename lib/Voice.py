import subprocess

class Voice:
    def __init__(self, voice):
        self.voice = voice

    def say(self, text, output_file=None):
        # Build the Flite command
        command = ["flite", "-t", text]
        command.extend(["-voice", self.voice])
        
        # Execute the command
        try:
            subprocess.run(command, check=True)
    
        except subprocess.CalledProcessError as e:
            print("Error while running Flite:", e)
