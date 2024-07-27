import random
from queue import Queue
from config import ENV, ModelConfig
from .Enum import Enum

class Intents:
  def __init__(self):
    self.__biases = Enum(
      blink = 1,
    )
    self.__intentsMap = ModelConfig.MODEL_OUTPUT_ANNOTATION
    self.__treshold = float(ENV.INTENTS_THRESHOLD)
    self.queue = Queue()

  def __addDeduped__(self, intentId, value):
    isDuplicate = False
    size = self.queue.qsize()
    for _ in range(size):
      item = self.queue.get()
      self.queue.put(item) 
      if item[0] == intentId:
        isDuplicate = True
    if isDuplicate == False:
      self.queue.put([intentId, value])

  def classify(self, decision):
    intents = {}
    for idx, score in enumerate(decision):
      if idx < len(self.__intentsMap):
        intents[self.__intentsMap[idx]] = score
    intents = sorted(intents.items(), key=lambda x: x[1], reverse=True)
    self.handleIntents(intents)

  def handleIntents(self, intents):
    handled = False
    # print('Intents:', intents);
    for intent in intents:
      intentId, value = intent
      if value > self.__treshold * random.uniform(0.75, 1.25):
        self.__addDeduped__([intentId, value])
        handled = True
      break
    
    if handled == False:
      self.queue.put(['noIntent', intents[0][1]])

  def setBias(self, key, value):
    self.__biases.set(key, value)
