import sys
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
from lib.ModelManager import ModelManager
from lib.Dictionary import Dictionary  # New Import
from config import Env, Paths

class AnimatronicRobot:
    def __init__(self):
        # 1. Initialize Manager and Load Brain
        try:
            self.manager = ModelManager(Paths)
            self.model, self.scaler = self.manager.load()
            
            # 2. Initialize the Dictionary helper
            self.dictionary = Dictionary(Paths.Dictionary)
            
            print("[System] Brain and Dictionary loaded successfully.")
        except Exception as e:
            print(f"[Fatal Error] Initialization failed: {e}")
            sys.exit(1)

        # 3. State Variables
        self.running = True
        self.is_currently_awake = 0
        self.last_awake_state = 0
        self.is_prompted = 0
        self.current_action = 0  
        self.last_spoke_time = 0 
        self.speech_lock = threading.Lock()

        # 4. Hardware/Voice Setup
        self.voice = Voice(Env.Voice, Env.VoiceSampleRate)

        # 5. Threading Handles
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
        """Uses Dictionary helper to fetch phrase and triggers TTS"""
        if category == "facts":
            # Combine intro and fact using Dictionary.pick
            intro = self.dictionary.pick("fact_intro", default="")
            fact = self.dictionary.pick("facts", default="I have no facts currently.")
            phrase = f"{intro} {fact}".strip()
        else:
            # Direct pick for 'hello', 'goodbye', etc.
            phrase = self.dictionary.pick(category)
        
        print(f"\n[ROBOT]: {phrase}")
        
        self.last_spoke_time = time.time()
        threading.Thread(target=self._threaded_say, args=(phrase,), daemon=True).start()

    def _brain_loop(self):
        """The Neural Network 'Think' Loop (20Hz)"""
        interval = 0.05 
        while self.running:
            start_time = time.time()

            time_since = (time.time() - self.last_spoke_time) / 60.0
            tod = self.get_time_decimal()
            
            raw_input = np.array([[self.is_currently_awake, self.is_prompted, time_since, tod]])
            
            try:
                scaled_input = self.scaler.transform(raw_input)
                self.current_action = self.model.predict(scaled_input)[0]
            except:
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
        robot.running = False