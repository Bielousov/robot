from copy import deepcopy
from lib.Enum import Enum
from lib.Sensors import Sensors

sensors = Sensors()

voiceBuffer = []

State = Enum (
  awake = 0,
)

def setState(key, value):
  State.set(key, value)

def getStateContext(state):
  context = deepcopy(state)
  context.cpuTemp = sensors.getCpuTemp()
  sensors.update()

def clearState():
  sensors.cleanup()