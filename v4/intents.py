import time
from datetime import datetime

class IntentHandler:
    def __init__(self, robot):
        self.robot = robot  # Reference to the main Pip instance
        print("[System] IntentHandler Initialized.")

    def handle(self):
        """Processes the current action state and triggers robot behaviors."""
        action = self.robot.current_action

        # --- PHASE 1: APPLY BRAIN DECISIONS ---
        if action == 1 and self.robot.is_currently_awake == 0:
            print("\n[Brain] Decision: WAKE UP")
            self.robot.is_currently_awake = 1
            self.robot.is_prompted = 0 

        elif action == 2 and self.robot.is_currently_awake == 1:
            print("\n[Brain] Decision: GO TO SLEEP")
            self.robot.is_currently_awake = 0
            self.robot.is_prompted = 0

        elif action == 3 and self.robot.is_currently_awake == 1:
            # Prevent rapid-fire talking
            if (time.time() - self.robot.last_spoke_time) > 3.0:
                print(f"\n[Brain] {datetime.now().strftime('%H:%M:%S')} Decision: SPEAK FACT")
                self.robot.speak("facts")
            self.robot.is_prompted = 0 

        # --- PHASE 2: SPEECH TRANSITIONS ---
        if self.robot.is_currently_awake == 1 and self.robot.last_awake_state == 0:
            self.robot.last_awake_state = 1
            self.robot.speak("hello")
        
        elif self.robot.is_currently_awake == 0 and self.robot.last_awake_state == 1:
            self.robot.last_awake_state = 0
            self.robot.speak("goodbye")