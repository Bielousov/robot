from datetime import datetime
from state import State
from errors import handelVerboseError

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
      response = self.openai.ask(State.pop('prompts'), onError=handelVerboseError)

      if response:
        State.append('utterances', response)

  def blink(self, confidenceScore):
    self.eyes.blink(confidenceScore)

  def say(self, confidenceScore):
    self.eyes.wonder()
    State.set('speaking', True)
    if State.utterances:
      if self.openai.ttsEnabled:
        self.openai.tts(State.pop('utterances'), onError=handelVerboseError)
      else:
        self.voice.say(State.pop('utterances'))
    State.set('speaking', False)

  def train(self, confidenceScore):
    self.eyes.wonder()
    self.intentsModel.trainAsync()

  def wakeup(self, confidenceScore):
    State.set('awake', True)
    self.eyes.open(confidenceScore)
    print('Waking up!')

  def noIntent(self, confidenceScore):
    return
  
