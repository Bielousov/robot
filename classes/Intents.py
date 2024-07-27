import random
from queue import Queue
from config import ENV, ModelConfig
from .Enum import Enum

class Intents:
  def __init__(self):
    self.__intentsMap = ModelConfig.MODEL_OUTPUT_ANNOTATION
    self.__treshold = float(ENV.INTENTS_THRESHOLD)
    self.__queue = Queue()

  def __addDeduped(self, intentId, value):
    isDuplicate = False
    size = self.__queue.qsize()
    for _ in range(size):
      item = self.__queue.get()
      self.__queue.put(item) 
      if item[0] == intentId:
        isDuplicate = True
    if isDuplicate == False:
      self.__queue.put([intentId, value])
    self.__queue.task_done()

  def __handleIntents(self, intents):
    handled = False
    # print('Intents:', intents);
    for intent in intents:
      intentId, value = intent
      if value > self.__treshold * random.uniform(0.75, 1.25):
        self.__addDeduped(intentId, value)
        handled = True
      break
    
    if handled == False:
      self.__queue.put(['noIntent', intents[0][1]])

  def classify(self, decision):
    intents = {}
    for idx, score in enumerate(decision):
      if idx < len(self.__intentsMap):
        intents[self.__intentsMap[idx]] = score
    intents = sorted(intents.items(), key=lambda x: x[1], reverse=True)
    self.__handleIntents(intents)

  def getIntent(self):
    return self.__queue.get()
  
  def doneProcessingIntent(self):
    return self.__queue.task_done()