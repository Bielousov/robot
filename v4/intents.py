import time
from datetime import datetime

class IntentHandler:
    def __init__(self, robot):
        self.robot = robot
        print("[System] IntentHandler Initialized.")

    def handle(self):
        action = self.robot.current_action

        # --- PHASE 1: ACTION EXECUTION ---
        if action == 1:
            print("[Brain] Action: WAKE UP")
            self.robot.is_awake_state = 1
            self.speak("hello")
        elif action == 2:
            print("[Brain] Action: SLEEP")
            self.robot.is_awake_state = 0
            self.speak("goodbye")
        elif action == 3:
            if not self.robot.is_speaking:
                self.speak("facts")

        # --- PHASE 2: STATE SYNCHRONIZATION ---
        # This is the most important line for the awake_phase logic!
        # It turns 'Transition' phases into 'Steady' phases for the next Brain tick.
        self.robot.is_awake_prev = self.robot.is_awake_state
        self.robot.is_prompted = 0
    

    def _on_speech_done(self, success, error=None):
        """Callback triggered when the Voice process finishes."""
        self.robot.is_speaking = False
        if error:
            print(f"[Voice Error] {error}")

    def speak(self, category):
        if self.robot.is_speaking:
            return # Guard clause: don't interrupt current speech

        if category == "facts":
            intro = self.robot.dictionary.pick("fact_intro", default="")
            fact = self.robot.dictionary.pick("facts", default="No facts.")
            phrase = f"{intro} {fact}".strip()
        else:
            phrase = self.robot.dictionary.pick(category)
        
        print(f"\n[ROBOT]: {phrase}")
        
        # Set the state and trigger voice with the callback
        self.robot.is_speaking = True
        self.robot.last_spoke_time = time.time()
        self.robot.voice.say(phrase, callback=self._on_speech_done)