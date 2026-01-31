import os, sys, random, time, threading
from datetime import datetime
import numpy as np

# Set the path for the v4 directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


from v4.lib.Voice import Voice

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
        print("Main control loop active. Press Ctrl+C to exit.")

        try:
            while True:
                simulated_awake_switch = 1 

                # 1. State Change Logic
                if simulated_awake_switch == 1 and self.is_currently_awake == 0:
                    self.speak("hello")
                    self.is_currently_awake = 1
                
                elif simulated_awake_switch == 0 and self.is_currently_awake == 1:
                    self.speak("goodbye")
                    self.is_currently_awake = 0

                # 2. Behavior Logic
                if self.is_currently_awake and self.current_action == 3:
                    # Fact Cooldown (30 seconds)
                    if (time.time() - self.last_spoke_time) > 30:
                        self.speak("facts")

                time.sleep(0.1)

        except KeyboardInterrupt:
            print("\nShutting down...")
            self.running = False

if __name__ == "__main__":
    robot = AnimatronicRobot()
    robot.run()