from random import random
from copy import deepcopy
from numpy import array
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
    context.cpuTemp,
    random(),
  ])

  print(result)

  return result

def clearState():
  sensors.cleanup()