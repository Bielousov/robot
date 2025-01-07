from config import ENV
from lib.Threads import Thread
from state import State, getStateContext

def EyesThread(eyes):
    threadInterval = 1 / int(ENV.EYES_FPS)

    def runThread():
      eyes.render()
    
    return Thread(threadInterval, runThread)

def IntentThread(intentHandler):
  threadInterval = 1 / int(ENV.INTENT_FPS)

  def runThread():
      if State.voiceQueue:
        intentHandler.say(State.voiceQueue.pop(0))
        return

      if State.promptQueue:
         intentHandler.ask(State.promptQueue.pop(0))
         
      
  return Thread(threadInterval, runThread)