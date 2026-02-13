import time
import numpy as np

from lib.Dictionary import Dictionary
from lib.Ears import Ears
from lib.Mind import Mind
from lib.ModelManager import ModelManager
from lib.Threads import Threads
from lib.Voice import Voice

from config import Env, Name, Paths
from intents import IntentHandler
from state import State

class Pip:
    def __init__(self):
        # 1. Load Brain model and Dictionary
        self.manager = ModelManager(Paths)
        self.model, self.scaler = self.manager.load()
        self.prompts = Dictionary(Paths.Prompts)
        self.state = State()
        
        # 2. Prefrontal Cortex (LLM)
        self.mind = Mind()

        # 2. Prefrontal Cortex (LLM)
        self.Ears = Ears(
            model_name=Env.VoskModel, 
            sample_rate=Env.VoskSampleRate,
            wake_word=Name,
            wake_word_synonyms=Env.VoskSynonyms,
            debug=Env.Debug
        )

        # 3. Voice Setup
        self.voice = Voice(
            voice_model_name=Env.Voice,
            voice_sample_rate=Env.VoiceSampleRate
        )
        
        # 4. Intent handler setup
        self.intent = IntentHandler(self)

        # 5. Custom Threading Manager
        self.threads = Threads()
        self.brain_thread = None
        self.logic_thread = None
        self.freq_thread = None
        self.listening_thread = None
    
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
                
                self.intent.handle(prediction)
                
        except Exception as e:
            print(f"Brain Error: {e}")

    def _brain_frequency_manager(self):
        """Adjust brain/logic thread intervals based on awake state.

        When `self.state.is_awake` is True we use `Env.BrainFrequencyGamma`,
        otherwise `Env.BrainFrequencyDelta`. Threads expect an interval value
        (seconds), so we use `1 / frequency` to match existing usage.
        """
        try:
            if self.state.is_awake:
                interval = 1 / Env.BrainFrequencyGamma
            else:
                interval = 1 / Env.BrainFrequencyDelta

            if self.brain_thread is not None:
                self.threads.set_interval(self.brain_thread, interval)
        except Exception as e:
            print(f"[Frequency Manager Error] {e}")
    
    def _on_wake_word(self, text, conversation_history):
        """Callback triggered by the Ears class when the wake word is detected."""
        # Get the current state of the ear's memory
        if text:
            last_captured = conversation_history[-1]
            print(f"\n[EVENT] Wake Word Detected!")
            print(f" > Message: {text}")
            print(f" > Last Captured: '{last_captured}'")
            
            for item in conversation_history:
                self.state.prompts.append(item)

    def run(self):
        # Create brain and logic threads and keep references so we can change
        # their intervals at runtime.
        self.brain_thread = self.threads.start(1 / Env.BrainFrequencyDelta, self._brain_tick)

        # Start a small manager that periodically enforces the desired
        # interval based on awake/sleep state.
        self.freq_thread = self.threads.start(1 / Env.BrainFrequencyDelta, self._brain_frequency_manager)

        # Start the Ears background process
        self.Ears.start_listening(self._on_wake_word)
        
        print("[System] All robot systems initialized")
    
    def stop(self):
        self.state.set_awake(False)
        print("[System] Shutting down...")
        time.sleep(1)
        self.Ears.stop_listening()
        self.voice.stop()
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