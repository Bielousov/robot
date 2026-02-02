import sys
import random
import time
from pathlib import Path

# Path Setup
v4_path = Path(__file__).parent.parent.parent.resolve()
if str(v4_path) not in sys.path:
    sys.path.insert(0, str(v4_path))

from config import Env

class Intent:
    """Handles the translation of Brain labels into robot actions/speech"""
    def __init__(self, robot, voice, vocab):
        self.robot = robot
        self.voice = voice
        self.vocab = vocab

    def speak(self, category):
        if category == "facts":
            intro = random.choice(self.vocab.get("fact_intro", [""]))
            fact = random.choice(self.vocab.get("facts", ["..."]))
            phrase = f"{intro} {fact}".strip()
        else:
            phrase = random.choice(self.vocab.get(category, ["..."]))
        
        print(f"\n[ROBOT]: {phrase}")
        self.voice.say(phrase)
        self.robot.last_spoke_time = time.time()

    def loop(self):
        print("[System] Intent/Logic Loop Active.")
        while self.robot.running:
            # --- PHASE 1: PROCESS BRAIN DECISIONS ---
            action = self.robot.current_action

            if action == 1 and self.robot.is_currently_awake == 0:
                print("\n[Brain] Decision: WAKE UP")
                self.robot.is_currently_awake = 1
                self.robot.is_prompted = 0 

            elif action == 2 and self.robot.is_currently_awake == 1:
                print("\n[Brain] Decision: GO TO SLEEP")
                self.robot.is_currently_awake = 0
                self.robot.is_prompted = 0

            elif action == 3 and self.robot.is_currently_awake == 1:
                print("\n[Brain] Decision: SPEAK FACT")
                self.speak("facts")
                self.robot.is_prompted = 0 

            # --- PHASE 2: STATE TRANSITIONS ---
            if self.robot.is_currently_awake == 1 and self.robot.last_awake_state == 0:
                self.speak("hello")
                self.robot.last_awake_state = 1
            
            elif self.robot.is_currently_awake == 0 and self.robot.last_awake_state == 1:
                self.speak("goodbye")
                self.robot.last_awake_state = 0

            time.sleep(0.1)