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

# Now you can import Voice normally
from lib.Voice import Voice

from config import ENV
import config_loader

class AnimatronicRobot:
    def __init__(self):
        # 1. Load Brain & Vocabulary via config_loader
        try:
            self.model, self.scaler = config_loader.load_brain()
            # Loading using the key "dictionary" as requested
            self.vocab = config_loader.load_json("dictionary")
            print("Brain and Vocabulary loaded successfully.")
        except Exception as e:
            print(f"Initialization Error: {e}")
            exit()

        # 2. State Variables
        self.last_spoke_time = time.time()
        self.is_currently_awake = 0
        self.current_action = 0  # 0: Nothing, 1: Hello, 2: Goodbye, 3: Fact
        self.running = True
        
        # 3. Threading Setup
        self.brain_thread = threading.Thread(target=self._brain_loop, daemon=True)

        # 4. Voice setup
        self.voice = Voice(ENV.VOICE)

    def get_time_decimal(self):
        now = datetime.now()
        return now.hour + (now.minute / 60.0)

    def speak(self, category):
        """Picks phrases and handles concatenation for facts"""
        if category == "facts":
            # Concatenate a random intro with a random fact
            intro = random.choice(self.vocab.get("fact_intro", [""]))
            fact = random.choice(self.vocab.get("facts", ["..."]))
            phrase = f"{intro} {fact}".strip()
        else:
            # Standard behavior for hello, goodbye, etc.
            phrase = random.choice(self.vocab.get(category, ["..."]))
        
        print(f"\n[ROBOT]: {phrase}")
        self.voice.say(phrase)
        self.last_spoke_time = time.time()

    def _brain_loop(self):
        """ The Neural Network 'Think' Loop running at 20Hz """
        interval = 0.05 
        while self.running:
            start_time = time.time()

            # Inputs: Awake=1, TimeSinceSpoke, TimeOfDay
            awake_input = 1 
            time_since = (time.time() - self.last_spoke_time) / 60.0
            tod = self.get_time_decimal()

            raw_input = np.array([[awake_input, time_since, tod]])
            scaled_input = self.scaler.transform(raw_input)
            
            self.current_action = self.model.predict(scaled_input)[0]

            elapsed = time.time() - start_time
            time.sleep(max(0, interval - elapsed))

    def run(self):
        self.brain_thread.start()
        print("Main control loop active. (Invoked via __main__)")

        # In this version, we don't catch KeyboardInterrupt here; 
        # we let it bubble up to __main__.py
        while self.running:
            # Simulate your switch (e.g., a physical toggle)
            simulated_awake_switch = 1 

            # State Change Logic (Transitional)
            if simulated_awake_switch == 1 and self.is_currently_awake == 0:
                self.speak("hello")
                self.is_currently_awake = 1
            
            # Note: The Goodbye logic is now handled in __main__.py 
            # or triggered by the switch turning to 0 here.
            elif simulated_awake_switch == 0 and self.is_currently_awake == 1:
                self.speak("goodbye")
                self.is_currently_awake = 0

            # Behavior Logic (Neural Net Decision)
            if self.is_currently_awake and self.current_action == 3:
                if (time.time() - self.last_spoke_time) > 30:
                    self.speak("facts")

            time.sleep(0.1)

if __name__ == "__main__":
    robot = AnimatronicRobot()
    robot.run()