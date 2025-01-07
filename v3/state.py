from random import random
from copy import deepcopy
from numpy import array, clip, log10
from lib.Enum import Enum
from lib.Sensors import Sensors
from dictionary import Responses
from utils import debug

sensors = Sensors()

State = Enum (
  awake = 0,
  promptQueue = [],
  voiceQueue = []
)

def setState(key, value):
  State.set(key, value)

def getStateContext():
  context = deepcopy(State)
  context.cpuTemp = sensors.getCpuTemp()
  context.noiseLevel = sensors.getNoise()
  sensors.update()

  result = array([
    context.awake,
    len(context.promptQueue),
    len(context.voiceQueue),
    normalizeCpuTemp(context.cpuTemp),
    context.noiseLevel,
    random(),
  ])

  debug(result, 'State')
  return result

def clearState():
  sensors.cleanup()

def handleError(error):  
  try:
    print(f"{error}: {Responses['errors'][error]}")
    State.voiceQueue.append(Responses['errors'][error])
  except:
      print(f"{error}: Unhandled error")
      State.voiceQueue.append(Responses['errors']['generic'])

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