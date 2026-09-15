import time
import numpy as np
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
        Matches training: [awake_phase, has_pending_prompt, is_thinking,
        has_pending_response, speaking]

        eavesdropped_context/time_since_heard/last_spoke_time_diff are
        deliberately not part of this vector - they only ever gated the
        spontaneous "utterance" behavior (label 4), which turned out to be a
        narrow region the classifier couldn't reliably separate from the
        broad "nothing to do" rules surrounding it (StandardScaler-normalized
        MLP decision boundaries washing out fine distinctions). That decision
        is now made directly in code (see Utterances.consider() in
        utterances.py), reading these properties straight off State instead.
        """
        return np.array([[
            self.awake_phase,
            self.has_pending_prompt,
            self.is_thinking,
            self.has_pending_response,
            self.is_speaking
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