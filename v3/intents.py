from datetime import datetime
from state import State

class IntentHandler:
  def __init__(self, eyes, intentsModel, openai, voice):
    self.eyes = eyes
    self.intentsModel = intentsModel
    self.openai = openai
    self.voice = voice

  def handle(self, intentId, confidenceScore):
    if intentId != 'noIntent':
      print(datetime.now().strftime('%H:%M:%S.%f')[:-3], 'Handling intent', intentId, 'with confidence', confidenceScore)
    return getattr(self, intentId, lambda: self.noIntent)()
  
  def ask(self):
    response = self.openai.ask(State.promptQueue.pop(0))
    self.eyes.wonder()

    if response:
      State.voiceQueue.append(response)

  def blink(self, confidenceScore):
    self.eyes.blink(confidenceScore)

  def say(self):
    if self.openai.ttsEnabled:
      self.openai.tts(State.voiceQueue.pop(0))
    else:
      self.voice.say(State.voiceQueue.pop(0))

    self.eyes.wonder()
  
  def train(self):
    self.eyes.wonder()
    self.intentsModel.train()

  def wakeup(self):
    self.eyes.open()

  def noIntent(self):
    return
