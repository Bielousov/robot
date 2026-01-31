import subprocess
import os
from pathlib import Path
from .Threads import Process

class Voice:
    def __init__(self, voice_model_name="en_US-lessac-medium.onnx"):
        self.__process = Process()
        
        # Resolve path: ./v4/lib/
        self.lib_path = Path(__file__).parent.absolute()
        
        # Piper binary: ./v4/lib/piper/piper
        self.piper_bin = self.lib_path / "piper" / "piper"
        
        # Voice models: ./v4/lib/piper/voices/
        self.model_path = self.lib_path / "piper" / "voices" / voice_model_name
        
        # Ensure the binary is executable
        if self.piper_bin.exists():
            os.chmod(self.piper_bin, 0o755)
        else:
            print(f"[Voice Warning]: Piper binary not found at {self.piper_bin}")

    def say(self, text, callback=None):
        # Escape double quotes to prevent shell injection/errors
        clean_text = text.replace('"', '\\"')
        
        # Piper pipeline
        # aplay flags: -r (rate), -f (format), -t (type)
        command = (
            f'echo "{clean_text}" | '
            f'{self.piper_bin} --model {self.model_path} --output_raw | '
            f'aplay -r 22050 -f S16_LE -t raw'
        )
        
        def _run():
            try:
                # shell=True enables the use of pipes (|)
                process = subprocess.Popen(
                    command, 
                    shell=True, 
                    stdout=subprocess.DEVNULL, 
                    stderr=subprocess.DEVNULL
                )
                return_code = process.wait()

                if callback:
                    callback(success=(return_code == 0))

            except Exception as e:
                print(f"[Voice Error]: {e}")
                if callback:
                    callback(success=False, error=str(e))

        # Run via your Process thread wrapper
        self.__process.run(_run)