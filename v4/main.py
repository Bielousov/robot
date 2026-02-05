import sys
import time
import threading

from pathlib import Path
import numpy as np


from lib.Voice import Voice
from lib.ModelManager import ModelManager
from lib.Dictionary import Dictionary  # New Import
from config import Env, Paths
from intents import IntentHandler
from utils import get_state_phase, get_time_decimal, get_time_since

class Pip:
    def __init__(self):
        # 1. Load Brain model and Dictionary
        self.manager = ModelManager(Paths)
        self.model, self.scaler = self.manager.load()
        self.dictionary = Dictionary(Paths.Dictionary)
        
        # 2. State Variables
        self.running = True
        self.is_awake_state = 0
        self.is_awake_prev = 0
        self.is_prompted = 0
        self.is_speaking = False
        self.current_action = 0  
        self.last_spoke_time = time.time()
        self.speech_lock = threading.Lock()

        # 3. Hardware/Voice Setup
        self.voice = Voice(Env.Voice, Env.VoiceSampleRate)

        # 4. Intent handler setup
        self.intent = IntentHandler(self)

        # 5. Threading Handles
        self.brain_thread = threading.Thread(target=self._brain_loop, daemon=True)
        self.logic_thread = threading.Thread(target=self._logic_loop, daemon=True)
    
    def _brain_loop(self):
        interval = 0.05 
        while self.running:
            # We must use a local copy of states to ensure atomicity during calculation
            current = self.is_awake_state
            last = self.is_awake_prev
            
            awake_phase = get_state_phase(current, last)
            
            raw_input = np.array([[
                float(awake_phase), 
                float(self.is_prompted), 
                1.0 if self.is_speaking else 0.0,
                get_time_since(self.last_spoke_time),
                get_time_decimal()
            ]])

            # print(f">>> {raw_input[0].tolist()}")
            
            try:
                scaled_input = self.scaler.transform(raw_input)
                self.current_action = self.model.predict(scaled_input)[0]
            except:
                pass

            time.sleep(interval)

    def _logic_loop(self):
        """The UI/Interaction Loop"""
        while self.running:
            self.intent.handle()
            time.sleep(0.1)

    def run(self):
        self.brain_thread.start()
        self.logic_thread.start()
        print("[System] All robot systems initialized.")

if __name__ == "__main__":
    robot = Pip()
    robot.run()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        robot.running = False