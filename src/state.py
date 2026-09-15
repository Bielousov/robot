import random, time
import numpy as np
from datetime import datetime
from collections import deque

from config import Env

class State:
    def __init__(self):
        self.is_awake = False
        self.is_awake_next = False
        self.last_spoke_time = time.time()
        self.last_heard_time = time.time()
        self.is_listening = False
        self.is_speaking = False
        self.is_thinking = False
        self.eavesdrop_limit = Env.EavesdropHistoryLimit
        self.eavesdrop = deque(maxlen=self.eavesdrop_limit)
        self.prompts = []
        self.responses = []

    @property
    def chaos(self):
        # Mostly small numbers; 0.99 becomes very rare.
        return random.triangular(0, 1, 0);

    @property
    def awake_phase (self):
        return self._get_state_phase(self.is_awake, self.is_awake_next)

    @property
    def has_pending_prompt(self):
        return 1.0 if len(self.prompts) > 0 else 0.0
    
    @property
    def has_pending_response(self):
        return 1.0 if len(self.responses) > 0 else 0.0

    @property
    def eavesdropped_context(self):
        """Total word count across all buffered eavesdropped utterances,
        capped at 100 (matches Robot Model training range) so a long-running
        conversation doesn't blow out the feature's scale."""
        word_count = sum(len(text.split()) for text in self.eavesdrop)
        return min(word_count, 100)

    @property
    def last_spoke_time_diff(self):
        return self._get_time_since(self.last_spoke_time, 3600)

    @property
    def time_since_heard(self):
        return self._get_time_since(self.last_heard_time, 60)

    @property
    def time_of_day(self):
        now = datetime.now()
        return now.hour + (now.minute / 60.0)

    def _get_state_phase(self, current, next):
        if current == next:
            return 1.0 if current else 0.0
        else:
            # Transitioning: 2 if just fell asleep, -1 if just woke up
            return 2.0 if next else -1.0

    def _get_time_since(self, t, max_value=None):
        seconds = int(time.time() - t)

        if max_value is not None:
            return min(seconds, max_value)

        return seconds


    def get_context(self):
        """
        Generates the input vector for the Neural Network.
        Matches training: [chaos, awake_phase, has_pending_prompt,
        eavesdropped_context, is_thinking, has_pending_response, speaking,
        time_since_spoke, time_since_heard, tod]
        """
        return np.array([[
            self.chaos, # chaos random input
            self.awake_phase,
            self.has_pending_prompt,
            self.eavesdropped_context,
            self.is_thinking,
            self.has_pending_response,
            self.is_speaking,
            self.last_spoke_time_diff,
            self.time_since_heard,
            self.time_of_day
        ]])

    def append_eavesdrop(self, text: str):
        """Append text to eavesdrop, maintaining max length limit automatically."""
        self.eavesdrop.append(text)
    
    def get_eavesdrop_context(self) -> list[str]:
        """Return eavesdrop history as a list of strings."""
        return list(self.eavesdrop)

    def set_awake(self, is_awake_next):
        self.is_awake_next = is_awake_next

    def set_last_spoke(self):
        self.last_spoke_time = time.time()

    def set_last_heard(self):
        self.last_heard_time = time.time()