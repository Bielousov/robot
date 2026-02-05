import sys
import time
import threading
from datetime import datetime
from pathlib import Path
import numpy as np


from lib.Voice import Voice
from lib.ModelManager import ModelManager
from lib.Dictionary import Dictionary  # New Import
from config import Env, Paths
from intents import IntentHandler

class Pip:
    def __init__(self):
        # 1. Load Brain model and Dictionary
        self.manager = ModelManager(Paths)
        self.model, self.scaler = self.manager.load()
        self.dictionary = Dictionary(Paths.Dictionary)
        
        # 2. State Variables
        self.running = True
        self.is_currently_awake = 0
        self.last_awake_state = 0
        self.is_prompted = 0
        self.current_action = 0  
        self.last_spoke_time = 0 
        self.speech_lock = threading.Lock()

        # 3. Hardware/Voice Setup
        self.voice = Voice(Env.Voice, Env.VoiceSampleRate)

        # 4. Intent handler setup
        self.intent = IntentHandler(self)

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