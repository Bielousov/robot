import subprocess
from .Threads import Process

class Voice:
    def __init__(self, voice):
        self.__process = Process()
        self.voice = voice

    def say(self, text, callback=None):
        # Build the Flite command
        command = [
            "flite",
            "-t", text, 
            "-voice", self.voice,
        ]
        
        def _run():
            try:
                thread = subprocess.Popen(command)
                return_code = thread.wait()

                if callback:
                    callback(
                        success=(return_code == 0)
                    )

            except Exception as e:
                if callback:
                    callback(success=False, error=e)


        # Run asynchronously via your thread wrapper
        self.__process.run(_run)