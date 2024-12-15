import numpy as np, os, sys, time

# Add the 'lib' directory to sys.path to ensurethat libs can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import ModelConfig, ENV
from intents import IntentHandler
from threads import DecisionThread, EyesThread, IntentsThread
from state import cleanupState
from lib.Decisions import Decisions
from lib.Eyes import Eyes
from lib.Intents import Intents
from lib.Threads import Threads

np.set_printoptions(suppress=True)

eyes = Eyes()
decisions = Decisions(
    modelPath = ModelConfig.MODEL_PATH,
    trainingSetPath = ModelConfig.MODEL_DATA_PATH,
    validationSetPath = ModelConfig.MODEL_DATA_VALIDATION_PATH,
    trainingEpochs = ENV.TRAINING_EPOCHS,
)
intentHandler = IntentHandler(decisions, eyes)
intents = Intents()
threads = Threads()

def run():
    decisions.setup()
    decisions.initializeModel()
    threads.start(EyesThread(eyes))
    threads.start(DecisionThread(decisions, intents))
    threads.start(IntentsThread(intents, intentHandler))
    print(ENV.NAME, "is here!")

def shutdown():
    print(ENV.NAME, "is leaving this world!")
    eyes.clear()
    time.sleep(0.5)
    threads.stop()
    cleanupState()
