from config import ENV
from state import State, getStateContext
from lib.Threads import Thread

def DecisionThread(decisions, intents):
  print('Starting a decisions thread at', ENV.DECISION_FPS, 'fps rate')
  threadInterval = 1 / int(ENV.DECISION_FPS)

  def runThread():
      context = getStateContext(State)
      intents.classify(decisions.run(context)[0])
      
  return Thread(threadInterval, runThread)


def IntentsThread(intents, intentHandler):
    print('Starting an intents queue thread at', ENV.INTENTS_FPS, 'fps rate')
    threadInterval = 1 / int(ENV.INTENTS_FPS)

    def runThread():
        intent, confidenceScore = intents.getIntent()
        intentHandler.handle(intent, confidenceScore)
        intents.doneProcessingIntent()
    
    return Thread(threadInterval, runThread)


def EyesThread(eyes):
    threadInterval = 1 / int(ENV.EYES_FPS)

    def runThread():
      eyes.render()
    
    return Thread(threadInterval, runThread)