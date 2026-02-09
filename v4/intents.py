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
        is_awake = self.robot.state.is_awake

        if action == 0:
            return
        
        # This is the most important line for the awake_phase logic!
        # It turns 'Transition' phases into 'Steady' phases for the next Brain tick.
        self.robot.state.is_awake_prev = self.robot.state.is_awake

        # Reset action after handling
        self.robot.state.current_action = 0 

        # --- PHASE 1: ACTION EXECUTION ---
        if action == 1: # WAKE UP
            self._debug("Action: WAKE UP")
            self.robot.state.is_awake = True
            self.speak("hello")
        elif action == 2: # SLEEP
            self._debug("Action: SLEEP")
            self.robot.state.is_awake = False
            self.speak("goodbye")
        elif action == 3: # PROMPT / UTTERANCE
            # If no prompt text exists, default to a random fact
            if not self.robot.state.prompts:
                self.speak("fact")
            else:
                prompt_text = self.robot.state.prompts.pop(0)
                if prompt_text == "quote":
                    self.speak("quote", True)
                else:
                    self.ask(prompt_text)

    def speak(self, category, contextual = False):
        self.robot.state.is_speaking = True
        prompt = self.robot.prompts.pick(category)
        answer = self.robot.mind.think(prompt, contextual)
        self.say(answer)

    def ask(self, prompt):
        self.robot.state.is_speaking = True
        answer = self.robot.mind.think(prompt)
        self.say(answer)

    def _on_speech_done(self, success, error=None):
        """Callback triggered when the Voice process finishes."""
        self.robot.state.is_speaking = False
        if error:
            self._debug(f"Voice Error: {error}", tag="Error")

    def say(self, phrase):
        self._debug(phrase, tag="ROBOT")

        if not phrase:
            return
        
        # Set the state and trigger voice with the callback
        self.robot.state.is_speaking = True
        self.robot.state.last_spoke_time = time.time()
        self.robot.voice.say(phrase, callback=self._on_speech_done)