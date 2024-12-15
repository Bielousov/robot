from config import ENV
from copy import deepcopy
from numpy import array
from classes.Enum import Enum
from classes.Sensors import Sensors

MAX_STATE_VALUE = 8
MIN_STATE_VALUE = 0

sensors = Sensors()

State = Enum (
  awake = 0,
  exhaust = 1,
  stress = 0,
)

def setState(key, value):
  State.set(key, value)

def setStateIncrease(key, value = 1):
  State.set(key, max(min(State.get(key) + value, MAX_STATE_VALUE), MIN_STATE_VALUE))

def getStateContext(state):
  context = deepcopy(state)
  context.cpuTemp = sensors.getCpuTemp()
  context.noiseLevel = sensors.getNoise()
  sensors.update()

  # print('context', [context.awake, context.exhaust, context.stress, context.cpuTemp, context.noiseLevel])

  return array([
    context.awake,
    context.exhaust,
    context.stress,
    context.cpuTemp,
    context.noiseLevel,
  ])

def cleanupState():
  sensors.cleanup()