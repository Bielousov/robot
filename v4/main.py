import sys
import time
import threading

from pathlib import Path
import numpy as np


from lib.Dictionary import Dictionary
from lib.LLMService import LLMService
from lib.ModelManager import ModelManager
from lib.Threads import Threads
from lib.Voice import Voice
from config import Env, ModelConfig, Paths
from intents import IntentHandler
from state import State

class Pip:
    def __init__(self):
        # 1. Load Brain model and Dictionary
        self.manager = ModelManager(Paths)
        self.model, self.scaler = self.manager.load()
        self.mind = LLMService()
        self.prompts = Dictionary(Paths.Prompts)
        
        # 2. State Variables
        self.state = State()
        
        # 3. Hardware/Voice Setup
        self.voice = Voice(Env.Voice, Env.VoiceSampleRate)

        # 4. Intent handler setup
        self.intent = IntentHandler(self)

        # 5. Custom Threading Manager
        self.threads = Threads()
    
    def _brain_tick(self):
        """One iteration of the brain logic"""
        context = self.state.get_context()
        try:
            scaled_input = self.scaler.transform(context)
            probabilities = self.model.predict_proba(scaled_input)[0]
            confidence = np.max(probabilities)
            prediction = np.argmax(probabilities)

            if confidence > Env.BrainConfidenceScore:
                if Env.Debug and prediction > 0:
                    formatted_str = ", ".join(
                        f"{x:.2f}".rstrip("0").rstrip(".")
                        for x in context[0].tolist()
                    )

                    print(
                        f"[DEBUG] Prediction: {prediction} "
                        f"with confidence {confidence * 100:.2f}%  "
                        f"[{formatted_str}]"
                    )
                
                self.state.current_action = prediction
            else:
                self.state.current_action = 0 
                
        except Exception as e:
            print(f"Brain Error: {e}")

    def _logic_tick(self):
        """One iteration of the intent handling"""
        self.intent.handle()

    def run(self):
        self.threads.start(1 / Env.BrainFrequency, self._brain_tick)
        self.threads.start(1 / Env.BrainFrequency, self._logic_tick)
        
        print("[System] All robot systems initialized")
    
    def stop(self):
        self.state.is_awake = False
        print("[System] Shutting down...")
        time.sleep(5)
        self.mind.stop()
        self.threads.stop()

if __name__ == "__main__":
    robot = Pip()
    robot.run()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        robot.stop()