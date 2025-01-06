from config import ENV
from lib.Threads import Thread
from state import State, getStateContext

def ChatThread(chatGPT):
    threadInterval = 1 / int(ENV.CHAT_FPS)

    def runThread():
      chatGPT.runQuery()
    
    return Thread(threadInterval, runThread)

def DecisionThread(decisions, intents):
  print('Starting a decisions thread at', ENV.DECISION_FPS, 'fps rate')
  threadInterval = 1 / int(ENV.DECISION_FPS)

  def runThread():
      context = getStateContext(State)
      intents.classify(decisions.run(context)[0])
      
  return Thread(threadInterval, runThread)

def EyesThread(eyes):
    threadInterval = 1 / int(ENV.EYES_FPS)

    def runThread():
      eyes.render()
    
    return Thread(threadInterval, runThread)

def VoiceThread(voice):
    threadInterval = 1 / int(ENV.VOICE_FPS)

    def runThread():
      voice.output()
    
    return Thread(threadInterval, runThread)