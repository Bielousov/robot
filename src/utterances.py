import random

from config import Env


class Utterances:
    """Decides the robot's spontaneous "free will" utterance behavior.

    Deliberately not one of the Robot Model's own classes (see
    State.get_context()'s docstring) - it's a filler behavior only worth
    considering when the model itself finds nothing else pressing to do
    ("Nothing"/action 0), so IntentHandler only ever calls consider() from
    its own action == 0 branch.
    """

    MIN_CONTEXT = 8
    MIN_SILENCE_S = 15
    RAMP_S = 30

    # _brain_tick calls consider() on every tick - tens of times a second
    # while awake (Env.BrainFrequencyGamma) - so even a 50/50 coin flip would
    # fire within a fraction of a second of becoming eligible. This is the
    # average real time between fires at full confidence (silence >=
    # RAMP_S), not "next tick": the per-tick probability is scaled down so
    # that, across all the ticks in that window, firing at least once is
    # about as likely as not.
    MEAN_SECONDS_TO_FIRE = 180  # ~3 minutes

    def __init__(self, robot):
        self.robot = robot

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
        """None if not eligible at all; otherwise a 0..1 confidence that
        ramps up the longer it's been quiet, approaching 1 as time since
        anything was last heard nears RAMP_S seconds.
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

        return min(state.time_since_heard / self.RAMP_S, 1.0)
