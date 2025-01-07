from random import random
from copy import deepcopy
from numpy import array, clip, log10
from lib.Enum import Enum
from lib.Sensors import Sensors

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
  # context.noiseLevel = sensors.getNoise()
  sensors.update()

  result = array([
    context.awake,
    len(context.promptQueue),
    len(context.voiceQueue),
    normalizeCpuTemp(context.cpuTemp),
    random(),
  ])

  print(result)

  return result

def clearState():
  sensors.cleanup()

def normalizeCpuTemp(temp):
    # Clip values to avoid errors (e.g., log(0))
    x = clip(temp, 1e-10, 1.0)  # Ensure values are within the range (0, 1]

    # Apply a logarithmic transformation
    transformed = log10(x + 1e-10)  # Logarithmic scaling

    # Normalize: Map 0.2 -> 0.2 and 0.4 -> 0.8
    minLog, maxLog = log10(0.2), log10(0.4)
    normalized = (transformed - minLog) / (maxLog - minLog)  # Rescale to [0, 1]
    scaled = normalized * (0.8 - 0.2) + 0.2  # Map [0, 1] to [0.2, 0.8]

    return clip(scaled, 0, 1)  # Ensure final bounds are within [0, 1]