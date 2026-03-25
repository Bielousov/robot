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

class Robot:
    def __init__(self):
        # 1. Load Brain model and Dictionary
        self.manager = ModelManager(Paths)
        self.model, self.scaler = self.manager.load()
        self.prompts = Dictionary(Paths.Prompts)
        self.quick_responses = Dictionary(Paths.Responses)
        self.state = State()
        
        # 2. Prefrontal Cortex (LLM)
        self.mind = Mind(
            conversation_history_length=Env.BrainContextLimit
        )

        # 2. Prefrontal Cortex (LLM)
        self.ears = Ears(
            debug=Env.Debug,
            model_name=Env.VoskModel, 
            sample_rate=Env.VoskSampleRate,
            wake_word=Name,
            wake_aliases=Env.VoskAliases,
            on_record=self._on_hear_speach,
            on_wake=self._on_wake_word,
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

    def _on_hear_speach(self, text: str = ""):
        """Callback for audio gating and recognized text handling.
        
        Called twice:
        1. With no text: gate check before Vosk processing
        2. With text: after speech recognition to append to eavesdrop
        """
        if text:
            # Text recognized - append to eavesdrop history (auto-limited)
            self.state.append_eavesdrop(text)
            self.state.set_last_spoke()
    
    def _on_wake_word(self, text: str):
        """Callback triggered by the Ears class when the wake word is detected."""
        if text:
            print(f"\n[EVENT] Wake Word Detected!")
            print(f" > Message: {text}")
            
            # Flatten eavesdrop context into a single prompt
            eavesdrop_context = self.state.get_eavesdrop_context()
            if eavesdrop_context:
                print(f" > Context: {eavesdrop_context}")
                self.state.prompts.append(eavesdrop_context)
            
            self.state.prompts.append(text)

    def run(self):
        # Create brain and logic threads and keep references so we can change
        # their intervals at runtime.
        self.brain_thread = self.threads.start(1 / Env.BrainFrequencyDelta, self._brain_tick)

        # Start a small manager that periodically enforces the desired
        # interval based on awake/sleep state.
        self.freq_thread = self.threads.start(1 / Env.BrainFrequencyDelta, self._brain_frequency_manager)

        # Start the Ears background process
        self.ears.start_listening()
        
        print("[System] All robot systems initialized")
    
    def stop(self):
        self.state.set_awake(False)
        print("[System] Shutting down...")
        time.sleep(1)
        self.threads.stop()
        self.ears.stop_listening()
        self.voice.stop()
        self.mind.stop()

if __name__ == "__main__":
    robot = Robot()
    robot.run()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        robot.stop()