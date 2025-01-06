from datetime import datetime
from state import setState, setStateIncrease

class IntentHandler:
  def __init__(self, decisions, eyes):
    self.eyes = eyes
    self.decisions = decisions

  def handle(self, intentId, confidenceScore):
    if intentId != 'noIntent':
      print(datetime.now().strftime('%H:%M:%S.%f')[:-3], 'Handling intent', intentId, 'with confidence', confidenceScore)
    return getattr(self, intentId, lambda: self.unhandledIntent)(confidenceScore)

  def blink(self, confidenceScore):
    self.eyes.blink(confidenceScore)

  def train(self, confidenceScore):
    self.eyes.wonder()
    self.decisions.train()

  def wakeup(self, confidenceScore):
    setState('awake', 1)
    print('Waking up!')
    self.eyes.open(confidenceScore)

  def noIntent(self, confidenceScore):
    setStateIncrease('exhaust', 0.01 )
    setStateIncrease('stress', -0.01)

  def unhandledIntent(self, confidenceScore):
    print('Unhandled intent', confidenceScore)
  
