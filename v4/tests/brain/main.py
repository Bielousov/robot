import sys, random, time, threading
from datetime import datetime
from pathlib import Path
import numpy as np

# Anchor to project root (v4)
# __file__ is v4/tests/brain/main.py
# .parent.parent.parent is /home/pip/projects/robot/v4/
v4_path = Path(__file__).parent.parent.parent.resolve()

if str(v4_path) not in sys.path:
    sys.path.insert(0, str(v4_path))

from lib.Voice import Voice

from config import ENV
import config_loader

class AnimatronicRobot:
    def __init__(self):
        try:
            self.model, self.scaler = config_loader.load_brain()
            self.vocab = config_loader.load_json("dictionary")
            print("Brain and Vocabulary loaded successfully.")
        except Exception as e:
            print(f"Initialization Error: {e}")
            exit()

        # State Variables
        self.last_spoke_time = time.time()
        self.is_currently_awake = 0
        self.last_awake_state = 0  # <--- ADD THIS LINE
        self.is_prompted = 0
        self.current_action = 0
        self.running = True
        
        self.brain_thread = threading.Thread(target=self._brain_loop, daemon=True)
        self.voice = Voice(ENV.VOICE)

    def get_time_decimal(self):
        now = datetime.now()
        return now.hour + (now.minute / 60.0)

    def speak(self, category):
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
        """ The Neural Network 'Think' Loop with 4 Inputs """
        interval = 0.05 
        while self.running:
            start_time = time.time()

            # Inputs: Awake, Prompted, TimeSinceSpoke, TimeOfDay
            awake_in = self.is_currently_awake 
            prompted_in = self.is_prompted
            time_since = (time.time() - self.last_spoke_time) / 60.0
            tod = self.get_time_decimal()

            # Now using 4 features
            raw_input = np.array([[awake_in, prompted_in, time_since, tod]])
            scaled_input = self.scaler.transform(raw_input)
            
            self.current_action = self.model.predict(scaled_input)[0]

            elapsed = time.time() - start_time
            time.sleep(max(0, interval - elapsed))

    def run(self):
        self.brain_thread.start()
        print("Main control loop active.")

        while self.running:
            # 1. State Change Logic (Transitional)
            # Check if we JUST woke up
            if self.is_currently_awake == 1 and self.last_awake_state == 0:
                print("[State] Transitioning to AWAKE")
                self.speak("hello")
                self.last_awake_state = 1
            
            # Check if we JUST fell asleep
            elif self.is_currently_awake == 0 and self.last_awake_state == 1:
                print("[State] Transitioning to SLEEP")
                self.speak("goodbye")
                self.last_awake_state = 0

            # 2. Behavior Logic (Neural Net Decision)
            # Logic for prompted wake-up (Label 1)
            if self.current_action == 1 and self.is_currently_awake == 0:
                self.is_currently_awake = 1
                self.is_prompted = 0
            
            # Logic for facts (Label 3)
            elif self.current_action == 3:
                # If it's a natural fact (not prompted), check the 30m timer
                # If it IS prompted, skip the timer.
                if self.is_prompted or (time.time() - self.last_spoke_time > 1800):
                    self.speak("facts")
                    self.is_prompted = 0 # Clear the flag

            time.sleep(0.1)
            
if __name__ == "__main__":
    robot = AnimatronicRobot()
    robot.run()