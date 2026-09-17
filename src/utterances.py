import random

import numpy as np

from config import Env, Paths
from lib.ModelManager import ModelManager


class Utterances:
    """Decides the robot's spontaneous "free will" utterance behavior.

    Deliberately not one of the Robot Model's own classes (see
    State.get_context()'s docstring) - it's a filler behavior only worth
    considering when the model itself finds nothing else pressing to do
    ("Nothing"/action 0), so IntentHandler only ever calls consider() from
    its own action == 0 branch.

    The confidence itself is neural-network-driven (see
    training/train_utterance.py) rather than a hand-written formula - a
    small MLPRegressor fit to a target surface over
    (eavesdropped_context, time_since_heard, time_of_day):

    - time_since_heard shapes a hump, not a monotonic ramp: confidence
      rises from MIN_SILENCE_S (don't cut off a conversation that just
      paused) up to a peak around 15s, then fades back down toward 0 by
      60s (the overheard context is stale by then - speaking up "late"
      about something no longer relevant feels wrong even with plenty of
      silence).
    - eavesdropped_context acts as a multiplier on that whole hump: with
      little overheard context, even the peak (~15s) stays low - only a
      lucky roll fires. With a lot of context, the multiplier is high
      enough that confidence is already substantial well before the peak,
      so it can fire earlier than 15s too.
    - time_of_day is a second multiplier: confidence is significantly
      lower overnight (ramping down from 21.5 to 24.0, back up from 0.0 to
      7.5) than during the day/evening (7.5-21.5, unaffected) - the robot
      shouldn't be as chatty in the middle of the night even if it's heard
      plenty and the room's been quiet a while.

    MIN_CONTEXT/MIN_SILENCE_S themselves stay hard gates here, in code,
    rather than something the model has to learn - they're step conditions
    ("not eligible at all" below either floor), and repeating the Robot
    Model's own `chaos`-removal lesson, MLPs fit curves well and hard steps
    poorly. Above both floors, the model's job is purely the graduated part.
    """

    MIN_CONTEXT = 8
    # True floor: never fire before this many seconds of silence, so a
    # brief pause mid-conversation is never mistaken for an opening.
    MIN_SILENCE_S = 5

    # _brain_tick calls consider() on every tick - tens of times a second
    # while awake (Env.BrainFrequencyGamma) - so even a 50/50 coin flip would
    # fire within a fraction of a second of becoming eligible. This is the
    # average real time between fires at full confidence, not "next tick":
    # the per-tick probability is scaled down so that, across all the ticks
    # in that window, firing at least once is about as likely as not.
    MEAN_SECONDS_TO_FIRE = 60  # ~1 minute

    def __init__(self, robot):
        self.robot = robot
        self.model, self.scaler = ModelManager(Paths).load(
            model_key="UtteranceModel", scaler_key="UtteranceModelScaler"
        )

    def consider(self):
        """Checks eligibility, then applies a confidence-weighted coin flip -
        eligible doesn't mean automatic. Returns True if an utterance was
        queued.
        """
        confidence = self._eligible_confidence()
        if confidence is None:
            return False

        # triangular(0, 1, 0) mirrors State's old `chaos` feature: mostly
        # small draws, large ones rare - keeps the coin flip biased toward
        # *not* firing even at high confidence, rather than a flat 50/50.
        # confidence is scaled down first (see _fire_scale) so that stacking
        # tens of these per second still averages out to MEAN_SECONDS_TO_FIRE
        # at full confidence, instead of firing within under a second.
        scaled_confidence = confidence * self._fire_scale()
        if scaled_confidence * random.triangular(0, 1, 0) > random.triangular(0, 1, 0):
            self.robot.state.prompts.append('utter')
            return True

        return False

    def _fire_scale(self):
        """Per-tick multiplier so repeated ticks land on MEAN_SECONDS_TO_FIRE
        on average, rather than the tick rate making it near-instant.

        With both draws ~ triangular(0, 1, 0), P(fire) = 2s/3 - s^2/6 for
        scale s; for the tiny s this resolves to, that's ~= 2s/3, so solving
        for a per-tick P(fire) of 1 / (ticks_per_second * MEAN_SECONDS_TO_FIRE)
        gives s ~= 1.5 / (ticks_per_second * MEAN_SECONDS_TO_FIRE).
        """
        ticks_per_second = max(Env.BrainFrequencyGamma, 1)
        return 1.5 / (ticks_per_second * self.MEAN_SECONDS_TO_FIRE)

    def _eligible_confidence(self):
        """None if not eligible at all; otherwise a 0..1 confidence from the
        trained model - higher with either more overheard context or more
        time since anything was last heard, so a lot of context can raise
        confidence even before time_since_heard alone would.
        """
        state = self.robot.state

        if not state.is_awake:
            return None
        if state.has_pending_prompt or state.has_pending_response:
            return None
        if state.is_thinking or state.is_speaking:
            return None
        if state.eavesdropped_context < self.MIN_CONTEXT:
            return None
        if state.time_since_heard < self.MIN_SILENCE_S:
            return None

        return self._predict_confidence(
            state.eavesdropped_context, state.time_since_heard, state.time_of_day
        )

    def _predict_confidence(self, eavesdropped_context, time_since_heard, time_of_day):
        """Runs the trained model for one (eavesdropped_context,
        time_since_heard, time_of_day) triple, clipped to [0, 1] since
        MLPRegressor's output isn't bounded and can slightly over/undershoot
        near the target surface's corners (0 at either floor, 1 once both
        ramps are maxed out and it's not the middle of the night).
        """
        x = np.array([[eavesdropped_context, time_since_heard, time_of_day]])
        x_scaled = self.scaler.transform(x)
        # Same harmless matmul over/underflow noise as during training (see
        # train_utterance.py's _fit_candidate) - this runs on every eligible
        # brain tick, so silence it here too rather than spamming the logs.
        with np.errstate(all='ignore'):
            prediction = float(self.model.predict(x_scaled)[0])
        return min(max(prediction, 0.0), 1.0)
