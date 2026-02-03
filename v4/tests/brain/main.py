import sys
import random
import time
import threading
from datetime import datetime
from pathlib import Path
import numpy as np

# Fix test paths
from test_helper import setup_test_env
setup_test_env()

from lib.Voice import Voice
from lib.ModelManager import ModelManager
from config import Env, Paths

class AnimatronicRobot:
    def __init__(self):
        # 1. Initialize Manager and Load Brain & Vocabulary
        try:
            # Using the new Manager to handle the heavy lifting
            self.manager = ModelManager(Paths)
            self.model, self.scaler = self.manager.load()
            
            # Using the direct-path JSON loader for the vocab
            self.vocab = self.manager._load_json(Paths.Dictionary)
            
            print("[System] Brain and Vocabulary loaded successfully via ModelManager.")
        except Exception as e:
            print(f"[Fatal Error] Initialization failed: {e}")
            sys.exit(1)

        # 2. State Variables
        self.running = True
        self.is_currently_awake = 0
        self.last_awake_state = 0
        self.is_prompted = 0
        self.current_action = 0  
        self.last_spoke_time = 0 
        self.speech_lock = threading.Lock() # Prevents overlapping speech threads

        # 3. Hardware/Voice Setup
        self.voice = Voice(Env.Voice, Env.VoiceSampleRate)

        # 4. Threading Handles
        self.brain_thread = threading.Thread(target=self._brain_loop, daemon=True)
        self.logic_thread = threading.Thread(target=self._logic_loop, daemon=True)

    def get_time_decimal(self):
        now = datetime.now()
        return now.hour + (now.minute / 60.0)

    def _threaded_say(self, phrase):
        """Internal helper to speak without blocking the logic loop"""
        with self.speech_lock:
            self.voice.say(phrase)

    def speak(self, category):
        """Fetches phrase and triggers non-blocking speech"""
        if category == "facts":
            intro = random.choice(self.vocab.get("fact_intro", [""]))
            fact = random.choice(self.vocab.get("facts", ["..."]))
            phrase = f"{intro} {fact}".strip()
        else:
            phrase = random.choice(self.vocab.get(category, ["..."]))
        
        print(f"\n[ROBOT]: {phrase}")
        
        # Update state immediately
        self.last_spoke_time = time.time()
        
        # Launch speech in background
        threading.Thread(target=self._threaded_say, args=(phrase,), daemon=True).start()

    def _brain_loop(self):
        """The Neural Network 'Think' Loop (20Hz)"""
        interval = 0.05 
        print(f"[System] Brain Loop Active at {1/interval}Hz")
        while self.running:
            start_time = time.time()

            # Inputs
            time_since = (time.time() - self.last_spoke_time) / 60.0
            tod = self.get_time_decimal()
            
            raw_input = np.array([[self.is_currently_awake, self.is_prompted, time_since, tod]])
            
            # Inference
            try:
                scaled_input = self.scaler.transform(raw_input)
                self.current_action = self.model.predict(scaled_input)[0]
            except Exception as e:
                # Silently catch inference blips during start-up
                pass

            elapsed = time.time() - start_time
            time.sleep(max(0, interval - elapsed))

    def _logic_loop(self):
        print("[System] Logic Loop Active.")
        while self.running:
            action = self.current_action

            # --- PHASE 1: APPLY BRAIN DECISIONS ---
            if action == 1 and self.is_currently_awake == 0:
                print("\n[Brain] Decision: WAKE UP")
                self.is_currently_awake = 1
                self.is_prompted = 0 

            elif action == 2 and self.is_currently_awake == 1:
                print("\n[Brain] Decision: GO TO SLEEP")
                self.is_currently_awake = 0
                self.is_prompted = 0

            elif action == 3 and self.is_currently_awake == 1:
                # Use a 3-second cooldown to protect the RPi 5 CPU/Power
                if (time.time() - self.last_spoke_time) > 3.0:
                    print(f"\n[Brain] {datetime.now().strftime('%H:%M:%S')} Decision: SPEAK FACT")
                    self.speak("facts")
                self.is_prompted = 0 

            # --- PHASE 2: SPEECH TRANSITIONS ---
            if self.is_currently_awake == 1 and self.last_awake_state == 0:
                self.last_awake_state = 1
                self.speak("hello")
            
            elif self.is_currently_awake == 0 and self.last_awake_state == 1:
                self.last_awake_state = 0
                self.speak("goodbye")

            time.sleep(0.1)

    def run(self):
        self.brain_thread.start()
        self.logic_thread.start()
        print("[System] All robot systems initialized.")

if __name__ == "__main__":
    robot = AnimatronicRobot()
    robot.run()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[System] Shutting down...")
        robot.running = False