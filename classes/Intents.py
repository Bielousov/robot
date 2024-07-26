import random
from queue import Queue
from config import ENV
from .Enum import Enum

class Intents:
  def __init__(self):
    self.__biases = Enum(
      blink = 1,
    )
    self.__intentsMap = [
      'wakeup',
      'train',
      'blink',
      'alert',
      'anger',
      'joy'
    ]
    self.__treshold = ENV.INTENTS_THRESHOLD * 1
    self.queue = Queue()

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
      if value > self.__treshold:
        self.queue.put([intentId, value])
        handled = True
      break
    
    if handled == False:
      self.queue.put(['noIntent', intents[0][1]])

  def setBias(self, key, value):
    self.__biases.set(key, value)
