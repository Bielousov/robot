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

    def handle(self, action):
        if action == 0:
            return

        # --- PHASE 1: ACTION EXECUTION ---
        if action == 1: # SLEEP
            self._debug("Action: SLEEP", tag="ROBOT")
            self._handle_sleep_intent();
        
        elif action == 2: # WAKE UP
            self._debug("Action: WAKE UP", tag="ROBOT")
            self._handle_wake_up_intent()
  
        elif action == 3: # PROMPT
            self._debug("Action: PROMPT", tag="ROBOT")
            prompts_to_process = self.robot.state.prompts[:]
            self.robot.state.prompts.clear()

            if prompts_to_process:
                self._handle_prompt_intent(prompts_to_process)
            else:
                self._debug("No prompts", tag="ROBOT")

        elif action == 4: # UTTERANCE
            self._debug("Action: UTTERANCE", tag="ROBOT")
            self._handle_utterance_intent()

        elif action == 5: # SPEAK
            self._debug("Action: SPEAK", tag="ROBOT")
            if self.robot.state.responses:
                message = self.robot.state.responses.pop(0)
                self._handle_speak_intent(message)
            else:
                self._debug("No response", tag="ROBOT")
        
        else:
            self._unhandled_intent(action)
    
    def _handle_sleep_intent(self): 
        self.robot.state.is_awake = False
        # self.robot.state.prompts.append("goodbye")

    def _handle_wake_up_intent(self): 
        self.robot.state.is_awake = True
        if not self.robot.state.prompts:
            self.robot.state.prompts.append("hello")
          
    def _handle_prompt_intent(self, raw_prompts):
        self.robot.state.is_thinking = True

        def callback(result, error=None):
            """Callback triggered when the LLM process finishes."""
            self.robot.state.is_thinking = False
            if result:
                self.robot.state.responses.append(result)
            if error:
                self._debug(f"LLM Error: {error}", tag="Error")

        processed_prompts = []
        for p in raw_prompts:
            if self.robot.prompts.has(p):
                # Replace key with a specific prompt from the dictionary category
                processed_prompts.append(self.robot.prompts.pick(p))
            else:
                processed_prompts.append(p)

        self.robot.mind.think(processed_prompts, callback)

    def _handle_utterance_intent(self):
         self.robot.state.prompts.append('utter')

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