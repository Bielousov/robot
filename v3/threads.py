from config import ENV
from lib.Threads import Thread

def EyesThread(eyes):
    threadInterval = 1 / int(ENV.EYES_FPS)

    def runThread():
      eyes.render()
    
    return Thread(threadInterval, runThread)