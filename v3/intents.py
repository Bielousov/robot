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
    return getattr(self, intentId, lambda: self.noIntent)()
  
  def ask(self, prompt,):
    response = self.openai.ask(prompt)
    self.eyes.wonder()

    if response:
      State.voiceQueue.append(response)

  def blink(self, confidenceScore):
    self.eyes.blink(confidenceScore)

  def say(self, text):
    if self.openai.ttsEnabled:
      self.openai.tts(text)
    else:
      self.voice.say(text)

    self.eyes.wonder()
  
  def train(self):
    self.eyes.wonder()
    self.intentsModel.train()

  def wakeup(self, text):
    self.eyes.open()

  def noIntent(self):
    return
