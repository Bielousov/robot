import os, sys, time, threading
from pathlib import Path


# Path Setup
v4_path = Path(__file__).parent.parent.parent.resolve()
if str(v4_path) not in sys.path:
    sys.path.insert(0, str(v4_path))

from lib.Dictionary import Dictionary
from lib.ModelManager import ModelManager
from lib.Voice import Voice

from .brain import Brain
from .config import Env, Paths
from .intent import Intent
# import config_loader

class Pip:
    def __init__(self):
        # 1. Shared State Variables
        self.running = True
        self.is_currently_awake = 0
        self.last_awake_state = 0
        self.is_prompted = 0
        self.current_action = 0
        self.last_spoke_time = 0

        # 2. Components
        self.dictionary = Dictionary(Paths.Dictionary)
        self.model = ModelManager({
            "model": Paths.Model,
            "scaler": Paths.ModelScaler,
        }, True)
        self.voice = Voice(Env.Voice, Env.VoiceSampleRate)
        
        # 3. Threading
        self.brain = Brain(self)
        self.intent = Intent(self, self.voice, self.dictionary)

        self.brain_thread = threading.Thread(target=self.brain.loop, daemon=True)
        self.logic_thread = threading.Thread(target=self.intent.loop, daemon=True)

    def run(self):
        self.brain_thread.start()
        self.logic_thread.start()
        print("[System] Robot brain and intent threads initialized.")

if __name__ == "__main__":
    robot = Pip()
    robot.run()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        robot.running = False