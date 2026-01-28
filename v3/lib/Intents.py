import random
from queue import Queue

class Intents:
  def __init__(self, annotations, threshold=0.51):
    self.__intentsMap = annotations
    self.__treshold = threshold
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

  def __handleIntents(self, intents):
    handled = False
    # print('Intents:', intents);
    for intent in intents:
      intentId, value = intent
      if value > self.__treshold * random.uniform(0.9, 1.1):
        self.__addDeduped(intentId, value)
        handled = True
      break
    
    if handled == False:
      self.__queue.put(['noIntent', intents[0][1]])

  def classify(self, result):
    intents = {}
    for idx, score in enumerate(result):
      if idx < len(self.__intentsMap):
        intents[self.__intentsMap[idx]] = score
    intents = sorted(intents.items(), key=lambda x: x[1], reverse=True)
    self.__handleIntents(intents)

  def getIntent(self):
    return self.__queue.get()
  
  def doneProcessingIntent(self):
    self.__queue.task_done()