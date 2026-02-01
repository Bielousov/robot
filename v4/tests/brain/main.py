import sys
import random
import time
import threading
from datetime import datetime
from pathlib import Path
import numpy as np

# Path Setup
v4_path = Path(__file__).parent.parent.parent.resolve()
if str(v4_path) not in sys.path:
    sys.path.insert(0, str(v4_path))

from lib.Voice import Voice
from config import Env
import config_loader

class AnimatronicRobot:
    def __init__(self):
        # 1. Load Brain & Vocabulary
        try:
            self.model, self.scaler = config_loader.load_brain()
            self.vocab = config_loader.load_json("dictionary")
            print("[System] Brain and Vocabulary loaded successfully.")
        except Exception as e:
            print(f"[Fatal Error] Initialization failed: {e}")
            sys.exit(1)

        # 2. State Variables
        self.running = True
        self.is_currently_awake = 0
        self.last_awake_state = 0
        self.is_prompted = 0
        self.current_action = 0  # 0: Nothing, 1: Hello, 2: Goodbye, 3: Fact
        self.last_spoke_time = 0 # Initialize at 0 to allow immediate first speech

        # 3. Hardware/Voice Setup
        self.voice = Voice(Env.Voice, Env.VoiceSampleRate)

        # 4. Threading Handles
        self.brain_thread = threading.Thread(target=self._brain_loop, daemon=True)
        self.logic_thread = threading.Thread(target=self._logic_loop, daemon=True)

    def get_time_decimal(self):
        now = datetime.now()
        return now.hour + (now.minute / 60.0)

    def speak(self, category):
        """Fetches phrase and sends to Voice library"""
        if category == "facts":
            intro = random.choice(self.vocab.get("fact_intro", [""]))
            fact = random.choice(self.vocab.get("facts", ["..."]))
            phrase = f"{intro} {fact}".strip()
        else:
            phrase = random.choice(self.vocab.get(category, ["..."]))
        
        print(f"\n[ROBOT]: {phrase}")
        self.voice.say(phrase)
        self.last_spoke_time = time.time()

    def _brain_loop(self):
        """ 
        The Neural Network 'Think' Loop (20Hz)
        Inputs: [Awake, Prompted, TimeSinceSpoke, TimeOfDay]
        """
        interval = 0.05 
        while self.running:
            start_time = time.time()

            # Inputs
            time_since = (time.time() - self.last_spoke_time) / 60.0
            tod = self.get_time_decimal()
            
            # This array MUST match your training columns: [awake, prompted, time, tod]
            raw_input = np.array([[self.is_currently_awake, self.is_prompted, time_since, tod]])
            
            # DEBUG: Uncomment this to see the "eyes" of the robot
            # print(f"[Brain Vision] Input: {raw_input} -> Action: {self.current_action}", end='\r')

            scaled_input = self.scaler.transform(raw_input)
            self.current_action = self.model.predict(scaled_input)[0]

            elapsed = time.time() - start_time
            time.sleep(max(0, interval - elapsed))

    def _logic_loop(self):
        """Pure Neural Network driven logic"""
        print("[System] Logic Loop Active.")
        while self.running:
            # --- PHASE 1: APPLY BRAIN DECISIONS FIRST ---
            # This updates the 'intent' before we check for speech transitions
            
            # Action 1: Brain wants to Wake Up
            if self.current_action == 1 and self.is_currently_awake == 0:
                print("\n[Brain] Decision: WAKE UP")
                self.is_currently_awake = 1
                self.is_prompted = 0 

            # Action 2: Brain wants to Sleep
            elif self.current_action == 2 and self.is_currently_awake == 1:
                print("\n[Brain] Decision: GO TO SLEEP")
                self.is_currently_awake = 0
                self.is_prompted = 0

            # Action 3: Brain wants to tell a Fact
            elif self.current_action == 3 and self.is_currently_awake == 1:
                print("\n[Brain] Decision: SPEAK FACT")
                self.speak("facts")
                self.is_prompted = 0 

            # --- PHASE 2: SPEECH TRANSITIONS ---
            # This triggers the 'Hello' or 'Goodbye' sounds based on the status
            if self.is_currently_awake == 1 and self.last_awake_state == 0:
                self.speak("hello")
                self.last_awake_state = 1
            
            elif self.is_currently_awake == 0 and self.last_awake_state == 1:
                self.speak("goodbye")
                self.last_awake_state = 0

            time.sleep(0.1)

    def run(self):
        """Starts the background threads and returns control to the caller"""
        self.brain_thread.start()
        self.logic_thread.start()
        print("[System] All robot systems initialized.")

if __name__ == "__main__":
    # If run directly for testing
    robot = AnimatronicRobot()
    robot.run()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        robot.running = False