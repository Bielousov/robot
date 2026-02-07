import random, time
from datetime import datetime
import numpy as np

class State:
    def __init__(self):
        self.is_awake = False
        self.is_awake_prev = False
        self.is_speaking = False
        self.last_spoke_time = time.time()
        self.current_action = 0
        self.prompts = []

    @property
    def chaos(self):
        return random.uniform(0, 1);

    @property
    def is_awake_phase (self):
        return self._get_state_phase(self.is_awake, self.is_awake_prev)

    @property
    def is_prompted(self):
        # The NN still needs a number. 1 if queue has items, 0 if empty.
        return 1.0 if len(self.prompts) > 0 else 0.0
    
    @property
    def last_spoke_diff(self):
        # The NN still needs a number. 1 if queue has items, 0 if empty.
        return self._get_time_since(self.last_spoke_time, 30)
    
    @property
    def time_of_day(self):
        now = datetime.now()
        return now.hour + (now.minute / 60.0)

    def _get_state_phase(self, current, last):
        if current == last:
            return 1.0 if current else 0.0
        else:
            # Transitioning: 2 if just fell asleep, -1 if just woke up
            return 2.0 if current else -1.0

    def _get_time_since(self, t, max_value=None):
        now = time.time()
        minutes = (now - t) / 60.0

        if max_value is not None:
            return min(minutes, max_value)

        return minutes


    def get_context(self):
        """
        Generates the input vector for the Neural Network.
        Matches training: [chaos, phase, prompted, speaking, time_since_spoke, tod]
        """   
        chaos = random.uniform(0, 1)
        return np.array([[
            self.chaos, # chaos random input 
            self.is_awake_phase,
            self.is_prompted,
            self.is_speaking,
            self.last_spoke_diff,
            self.time_of_day,
        ]])