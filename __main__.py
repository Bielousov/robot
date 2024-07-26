import numpy as np, signal, sys, time

from config import Config, ENV
from intents import IntentHandler
from threads import DecisionThread, EyesThread, IntentsThread
from state import cleanupState
from classes.Decisions import Decisions
from classes.Eyes import Eyes
from classes.Intents import Intents
from classes.Threads import Threads

np.set_printoptions(suppress=True)

eyes = Eyes()
decisions = Decisions(
    modelPath = Config.MODEL_PATH,
    trainingSetPath = Config.MODEL_DATA_PATH,
    validationSetPath = Config.MODEL_DATA_VALIDATION_PATH,
    trainingEpochs = ENV.TRAINING_EPOCHS,
)
intentHandler = IntentHandler(decisions, eyes)
intents = Intents()
threads = Threads()

def startup():
    decisions.setup()
    decisions.initializeModel()
    threads.start(EyesThread(eyes))
    threads.start(DecisionThread(decisions, intents))
    threads.start(IntentsThread(intents, intentHandler))
    print(ENV.NAME, "is here!")

def shutdown():
    print(ENV.NAME, "is leaving this world!")
    eyes.clear()
    time.spleep(0.5)
    threads.stop()
    cleanupState()

def exitSignal(signal, frame):
    print("Handling exit signal:",signal)
    shutdown()
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, exitSignal)
    signal.signal(signal.SIGTERM, exitSignal)
    startup()
