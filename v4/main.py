import sys
import time
import threading

from pathlib import Path
import numpy as np


from lib.Voice import Voice
from lib.ModelManager import ModelManager
from lib.Dictionary import Dictionary  # New Import
from config import Env, ModelConfig, Paths
from intents import IntentHandler
from state import State

class Pip:
    def __init__(self):
        # 1. Load Brain model and Dictionary
        self.manager = ModelManager(Paths)
        self.model, self.scaler = self.manager.load()
        self.dictionary = Dictionary(Paths.Dictionary)
        
        # 2. State Variables
        self.state = State()
        self.running = True
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
            context = self.state.get_context()

            try:
                # Process through the brain
                scaled_input = self.scaler.transform(context)

                probabilities = self.model.predict_proba(scaled_input)[0]
                confidence = np.max(probabilities)
                prediction = np.argmax(probabilities)

                if confidence > ModelConfig.BRAIN_CONFIDENCE_THRESHOLD:
                    if Env.Debug & prediction > 0:
                        print(f">>> {[f"{x:.4f}" for x in context[0].tolist()]}")
                        print(f"Prediction: {prediction} with confidence {confidence * 100}%")
                    self.state.current_action = prediction
                else:
                    self.state.current_action = 0 # Default to Nothing

                # self.state.current_action = self.model.predict(scaled_input)[0]
            except Exception as e:
                print(f"Brain Error: {e}")
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