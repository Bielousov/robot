from config import ENV, MODEL
from lib.Intents import Intents
from lib.Threads import Thread
from state import State, getStateContext

def EyesThread(eyes):
    threadInterval = 1 / int(ENV.EYES_FPS)

    def runThread():
      eyes.render()
    
    return Thread(threadInterval, runThread)

def IntentsThread(intentsModel, intentHandler):
  intents = Intents(
    annotations=MODEL.INTENT_ANNOTATION,
    threshold=MODEL.INTENT_THRESHOLD,
  )

  threadInterval = 1 / int(ENV.INTENT_FPS)

  def runThread():
      context = getStateContext()
      intents.classify(intentsModel.run(context)[0])
      intent, confidenceScore = intents.getIntent()
      intentHandler.handle(intent, confidenceScore)
      intents.doneProcessingIntent()
      
  return Thread(threadInterval, runThread)