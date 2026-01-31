from config import ENV, MODEL
from v3.lib.Intents import Intents
from v3.lib.Threads import Thread
from state import getStateContext

def EyesThread(eyes, threads):
  threadInterval = 1 / int(ENV.EYES_FPS)

  def runThread():
    print("running eyes thread")
    eyes.render()
    
  print(f"setting up eyes thread {threadInterval}")
  return Thread(threadInterval, runThread, threads.run_event)

def IntentsThread(intentsModel, intentHandler, threads):
  intents = Intents(
    annotations=MODEL.INTENT_ANNOTATION,
    threshold=MODEL.INTENT_THRESHOLD,
  )

  threadInterval = 1 / int(ENV.INTENT_FPS)

  def runThread():
    print("running intents thread")
    context = getStateContext()
    intents.classify(intentsModel.run(context)[0])
    intent, confidenceScore = intents.getIntent()
    intentHandler.handle(intent, confidenceScore)
    intents.doneProcessingIntent()
      
  print(f"setting up intents thread {threadInterval}")
  return Thread(threadInterval, runThread, threads.run_event)