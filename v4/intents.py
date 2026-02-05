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
        if action == 1:
            self._debug("Action: WAKE UP")
            self.robot.state.is_awake_state = True
            self.speak("hello")
        elif action == 2:
            self._debug("Action: SLEEP")
            self.robot.state.is_awake_state = False
            self.speak("goodbye")
        elif action == 3:
            if not self.robot.state.is_speaking:
                self.speak("facts")

        # --- PHASE 2: STATE SYNCHRONIZATION ---
        # This is the most important line for the awake_phase logic!
        # It turns 'Transition' phases into 'Steady' phases for the next Brain tick.
        self.robot.state.is_awake_prev = self.robot.state.is_awake_state
        self.robot.state.is_prompted = False
    

    def _on_speech_done(self, success, error=None):
        """Callback triggered when the Voice process finishes."""
        self.robot.state.is_speaking = False
        if error:
            self._debug(f"Voice Error: {error}", tag="Error")

    def speak(self, category):
        if self.robot.state.is_speaking:
            return # Guard clause: don't interrupt current speech

        if category == "facts":
            intro = self.robot.dictionary.pick("fact_intro", default="")
            fact = self.robot.dictionary.pick("facts", default="No facts.")
            phrase = f"{intro} {fact}".strip()
        else:
            phrase = self.robot.dictionary.pick(category)
        
        self._debug(phrase, tag="ROBOT")
        
        # Set the state and trigger voice with the callback
        self.robot.state.is_speaking = True
        self.robot.state.last_spoke_time = time.time()
        self.robot.voice.say(phrase, callback=self._on_speech_done)