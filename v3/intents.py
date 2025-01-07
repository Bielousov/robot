from datetime import datetime
from state import setState, setStateIncrease, State

class IntentHandler:
  def __init__(self, eyes, openai, voice):
    self.eyes = eyes
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
    self.voice.say(text)
    self.eyes.wonder()

  def noIntent(self):
    return
