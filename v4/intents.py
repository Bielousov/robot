import time
from datetime import datetime

class IntentHandler:
    def __init__(self, robot):
        self.robot = robot
        self._debug("IntentHandler Initialized.", tag="System")

    def _debug(self, message, tag="Intent"):
        """Centralized logging with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{tag}] {message}")

    def handle(self):
        action = self.robot.state.current_action

        if action == 0:
            return

        # --- PHASE 1: ACTION EXECUTION ---
        if action == 1: # WAKE UP
            self._debug("Action: WAKE UP")
            self.robot.state.is_awake = True
            self.speak("hello")
        elif action == 2: # SLEEP
            self._debug("Action: SLEEP")
            self.robot.state.is_awake = False
            self.speak("goodbye")
        elif action == 3: # PROMPT
            if len(self.robot.state.prompts) > 0:
                prompt_text = self.robot.state.prompts.pop(0)
                
                if not prompt_text or prompt_text == "trigger_fact":
                    self.speak("facts")
                else:
                    # This is where your Microphone/STT results will land
                    self.say(prompt_text)

        # --- PHASE 2: STATE SYNCHRONIZATION ---
        # This is the most important line for the awake_phase logic!
        # It turns 'Transition' phases into 'Steady' phases for the next Brain tick.
        self.robot.state.is_awake_prev = self.robot.state.is_awake

        # Reset action after handling
        self.robot.state.current_action = 0 
    

    def _on_speech_done(self, success, error=None):
        """Callback triggered when the Voice process finishes."""
        self.robot.state.is_speaking = False
        if error:
            self._debug(f"Voice Error: {error}", tag="Error")

    def speak(self, category):
        if self.robot.state.is_speaking:
            return

        if category == "facts":
            intro = self.robot.dictionary.pick("fact_intro", default="")
            fact = self.robot.dictionary.pick("facts", default="No facts.")
            phrase = f"{intro} {fact}".strip()
        else:
            phrase = self.robot.dictionary.pick(category)

        self.say(phrase)
    
    def say(self, phrase):
        self._debug(phrase, tag="ROBOT")

        # Set the state and trigger voice with the callback
        self.robot.state.is_speaking = True
        self.robot.state.last_spoke_time = time.time()
        self.robot.voice.say(phrase, callback=self._on_speech_done)