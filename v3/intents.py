from datetime import datetime
from state import appendState, popState, setState, State

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
    if State.prompts:
      response = self.openai.ask(popState('prompts'))

      if response:
        appendState('utterances', response)

  def blink(self, confidenceScore):
    self.eyes.blink(confidenceScore)

  def say(self, confidenceScore):
    self.eyes.wonder()
    setState('speaking', True)
    if State.utterances:
      if self.openai.ttsEnabled:
        self.openai.tts(popState('utterances'))
      else:
        self.voice.say(popState('utterances'))
    setState('speaking', False)

  def train(self, confidenceScore):
    self.eyes.wonder()
    self.intentsModel.train()

  def wakeup(self, confidenceScore):
    setState('awake', True)
    self.eyes.open(confidenceScore)
    print('Waking up!')

  def noIntent(self, confidenceScore):
    return
  
