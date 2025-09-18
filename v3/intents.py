from datetime import datetime
from lib.LocalDictionary import LocalDictionary
from state import State
from errors import handelVerboseError

class IntentHandler:
  def __init__(self, eyes, intentsModel, openai, voice):
    self.eyes = eyes
    self.intentsModel = intentsModel
    self.openai = openai
    self.voice = voice

  def __cache(self):
    return LocalDictionary("responses.db");

  def handle(self, intentId, confidenceScore):
    if intentId != 'noIntent':
      print(datetime.now().strftime('%H:%M:%S.%f')[:-3], 'Handling intent', intentId, 'with confidence', confidenceScore)
    return getattr(self, intentId, lambda: self.noIntent)(confidenceScore)

  def ask(self, confidenceScore):
    self.eyes.wonder()
    if State.prompts:
      prompt = State.pop('prompts')
      cache = self.__cache()
      promptCacheSize = cache.count(prompt)
      localResponse = cache.getSome(prompt)

      # Check responses in local dictionary
      if (promptCacheSize >= self.openai.cacheLimit):
        State.append('utterances', localResponse)
        return
      
      # Prompt openai
      else:
        aiResponse = self.openai.ask(
          prompt,
          onError=lambda: State.append('utterances', localResponse) if localResponse else handelVerboseError()
        )
        if aiResponse:
          State.append('utterances', aiResponse)

          # save response to local dictionary
          if (not cache.exists(prompt, aiResponse)):
            cache.set(prompt, aiResponse)

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
  
