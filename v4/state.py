import random, time
from datetime import datetime
import numpy as np

class State:
    def __init__(self):
        self.is_awake_state = False
        self.is_awake_prev = False
        self.is_prompted = False
        self.is_speaking = False
        self.last_spoke_time = time.time()
        self.current_action = 0

    def _get_boolean_context(self, bool):
        return 1.0 if bool else 0.0

    def _get_state_phase(self, current, last):
        if current == last:
            return 1.0 if current else 0.0
        else:
            # Transitioning: 2 if just fell asleep, -1 if just woke up
            return 2.0 if current else -1.0
    
    def _get_time_decimal(self):
        now = datetime.now()
        return now.hour + (now.minute / 60.0)


    def _get_time_since(self, t):
        now = time.time()
        return (now - t) / 60.0


    def get_context(self):
        """
        Generates the input vector for the Neural Network.
        Matches training: [chaos, phase, prompted, speaking, time_since, tod]
        """   
        chaos = random.uniform(0, 1)
        return np.array([[
            chaos, # chaos random input 
            self._get_state_phase(self.is_awake_state, self.is_awake_prev),
            self._get_boolean_context(self.is_prompted),
            self._get_boolean_context(self.is_speaking),
            self._get_time_since(self.last_spoke_time),
            self._get_time_decimal()
        ]])