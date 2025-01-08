from random import random
from copy import deepcopy
from numpy import array, clip, log10
from lib.Enum import Enum
from lib.Sensors import Sensors
from config import ENV
from dictionary import Responses
from utils import debug

sensors = Sensors(debug = ENV.DEBUG)

State = Enum (
  awake = False,
  speaking = False,

  # queues
  prompts = [],
  utterances = [],

  # sensors
  ambientNoise = 0,
  cpuTemp = 0,
)

def updateSensors():
  sensors.update()
  State.ambientNoise = sensors.getNoise()
  State.cpuTemp = sensors.getCpuTemp()

def appendState(key, value):
  State[key].append(value)

def popState(key):
  return State[key].pop(0)

def setState(key, value):
  State.set(key, value)

def getStateContext():
  updateSensors()

  result = array([
    1 if State.awake else 0,
    len(State.prompts),
    len(State.utterances),
    normalizeCpuTemp(State.cpuTemp),
    State.ambientNoise,
    random(),
  ])

  debug(result, 'State')
  return result

def clearState():
  sensors.cleanup()

def handleError(error):  
  try:
    print(f"{error}: {Responses['errors'][error]}")
    appendState('utterances', Responses['errors'][error])
  except:
    print(f"{error}: Unhandled error")
    appendState('utterances', Responses['errors']['generic'])

def normalizeCpuTemp(temp, minValue=0.2, maxValue=0.4):
    # Clip values to avoid errors (e.g., log(0))
    x = clip(temp, 1e-10, 1.0)  # Ensure values are within the range (0, 1]

    # Apply a logarithmic transformation
    transformed = log10(x + 1e-10)  # Logarithmic scaling

    # Normalize: Map 0.2 -> 0.1 and 0.3 -> 0.9
    minLog, maxLog = log10(minValue), log10(maxValue)
    normalized = (transformed - minLog) / (maxLog - minLog)  # Rescale to [0, 1]
    scaled = normalized * (0.9 - 0.1) + 0.1  # Map [0, 1] to [0.1, 0.9]

    return clip(scaled, 0, 1)  # Ensure final bounds are within [0, 1]