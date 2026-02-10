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
        
        # It turns 'Transition' phases into 'Steady' phases for the next Brain tick.
        self.robot.state.is_awake_prev = self.robot.state.is_awake

        # Reset action after handling
        self.robot.state.current_action = 0 

        # --- PHASE 1: ACTION EXECUTION ---
        if action == 1: # SLEEP
            self._debug("Action: SLEEP", tag="ROBOT")
            self._handle_sleep_intent();
        
        elif action == 2: # WAKE UP
            self._debug("Action: WAKE UP", tag="ROBOT")
            self._handle_wake_up_intent()
  
        elif action == 3: # PROMPT / UTTERANCE
            self._debug("Action: PROMPT", tag="ROBOT")
            prompt = "quote" if not self.robot.state.prompts else self.robot.state.prompts.pop(0)
            self._handle_prompt_intent(prompt)

        elif action == 4: # SPEAK
            self._debug("Action: SPEAK", tag="ROBOT")
            message = self.robot.state.responses.pop(0)
            self._handle_speak_intent(message)
        
        else:
            self._unhandled_intent(action)
    
    def _handle_sleep_intent(self): 
        self.robot.state.is_awake = False
        self.robot.state.prompts.append("goodbye")

    def _handle_wake_up_intent(self): 
        self.robot.state.is_awake = True
        self.robot.state.prompts.append("hello")
          
    def _handle_prompt_intent(self, prompt):
        self.robot.state.is_thinking = True

        def callback(result, error=None):
            """Callback triggered when the LLM process finishes."""
            self.robot.state.is_thinking = False
            if result:
                self.robot.state.responses.append(result)
            if error:
                self._debug(f"LLM Error: {error}", tag="Error")

        if self.robot.prompts.has(prompt):
            category = self.robot.prompts.pick(prompt)
            self.robot.mind.think(category, callback)
        else:
            self.robot.mind.think(prompt, callback)

    def _handle_speak_intent(self, phrase):
        if not phrase:
            return
        
        def callback(success, error=None):
            """Callback triggered when the Voice process finishes."""
            self.robot.state.is_speaking = False
            if error:
                self._debug(f"Voice Error: {error}", tag="Error")

        # Set the state and trigger voice with the callback
        self.robot.state.is_speaking = True
        self.robot.state.last_spoke_time = time.time()
        self.robot.voice.say(phrase, callback)
        self._debug(f"Saying: {phrase}", tag="ROBOT")

    def _unhandled_intent(self, intent):
        self._debug(f"Unhandled Intent $intent")
        return