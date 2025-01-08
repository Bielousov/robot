from datetime import datetime
from state import setState, State

class IntentHandler:
  def __init__(self, eyes, intentsModel, openai, voice):
    self.eyes = eyes
    self.intentsModel = intentsModel
    self.openai = openai
    self.voice = voice

  def handle(self, intentId, confidenceScore):
    if intentId != 'noIntent':
      print(datetime.now().strftime('%H:%M:%S.%f')[:-3], 'Handling intent', intentId, 'with confidence', confidenceScore)
    return getattr(self, intentId, lambda: self.noIntent)(confidenceScore)
  
  def ask(self, confidenceScore):
    self.eyes.wonder()
    if State.promptQueue:
      response = self.openai.ask(State.promptQueue.pop(0))

      if response:
        State.voiceQueue.append(response)

  def blink(self, confidenceScore):
    self.eyes.blink(confidenceScore)

  def say(self, confidenceScore):
    self.eyes.wonder()
    if State.voiceQueue:
      if self.openai.ttsEnabled:
        self.openai.tts(State.voiceQueue.pop(0))
      else:
        self.voice.say(State.voiceQueue.pop(0))

  def train(self, confidenceScore):
    self.eyes.wonder()
    self.intentsModel.train()

  def wakeup(self, confidenceScore):
    setState('awake', 1)
    self.eyes.open(confidenceScore)
    print('Waking up!')

  def noIntent(self, confidenceScore):
    return
  
