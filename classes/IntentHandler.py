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

  def alert(self, confidenceScore):
    setStateIncrease('exhaust', confidenceScore / 4 )
    setStateIncrease('stress', confidenceScore / 4)
    self.eyes.focus(0,0)

  def anger(self, confidenceScore):
    setStateIncrease('exhaust', confidenceScore / 4 )
    setStateIncrease('stress', -confidenceScore / 2)

  def blink(self, confidenceScore):
    setStateIncrease('exhaust', -confidenceScore )
    setStateIncrease('stress', -0.1)
    self.eyes.blink(confidenceScore)

  def joy(self, confidenceScore):
    # TODO: smile
    setStateIncrease('exhaust', -confidenceScore )
    setStateIncrease('stress', - confidenceScore)

  def train(self, confidenceScore):
    self.eyes.wonder()
    trainSuccess = self.decisions.train()
    setStateIncrease('exhaust', confidenceScore / 10 )
    if trainSuccess == True:
      setStateIncrease('stress', -confidenceScore / 4)
    else:
      setStateIncrease('stress', confidenceScore / 4)
      setStateIncrease('exhaust', confidenceScore / 4 )

  def wakeup(self, confidenceScore):
    setState('awake', 1)
    setState('exhaust', 0)
    setState('stress', 0 )
    print('Waking up!')
    self.eyes.open(confidenceScore)

  def noIntent(self, confidenceScore):
    setStateIncrease('exhaust', 0.01 )
    setStateIncrease('stress', -0.01)

  def unhandledIntent(self, confidenceScore):
    print('Unhandled intent', confidenceScore)
  
