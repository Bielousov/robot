from config import ENV
from lib.Threads import Thread

def ChatThread(chatGPT):
    threadInterval = 1 / int(ENV.CHAT_FPS)

    def runThread():
      chatGPT.runQuery()
    
    return Thread(threadInterval, runThread)

def EyesThread(eyes):
    threadInterval = 1 / int(ENV.EYES_FPS)

    def runThread():
      eyes.render()
    
    return Thread(threadInterval, runThread)