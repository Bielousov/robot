from random import random
from copy import deepcopy
from numpy import array, clip, log10
from lib.Sensors import Sensors
from config import ENV
from utils import debug

sensors = Sensors(debug = ENV.DEBUG)

class StateClass():
  def __init__(self):
    self.awake = False
    self.on = True
    self.speaking = False

    # queues
    self.prompts = []
    self.utterances = []

    # sensors
    self.ambientNoise = 0
    self.cpuTemp = 0

  def get(self, key):
    if hasattr(self, key):
      getattr(self, key)
    else:
      raise AttributeError(f"'{key}' is not a valid property of {self.__class__.__name__}")

  def set(self, key, value):
    if hasattr(self, key):
      setattr(self, key, value)
    else:
      raise AttributeError(f"'{key}' is not a valid property of {self.__class__.__name__}")

  def append(self, key, value):
    if hasattr(self, key):
      getattr(self, key).append(value)
    else:
      raise AttributeError(f"{key} is not a valid attribute of {self.__class__.__name__}.")

  def pop(self, key):
    if hasattr(self, key):
      return getattr(self, key).pop(0)
    else:
      raise AttributeError(f"{key} is not a valid attribute of State.")

# Singleton State instance
State = StateClass()

def getStateContext():
  try:
    State.set('ambientNoise', sensors.getNoise())
    State.set('cpuTemp', sensors.getCpuTemp())
  except:
    print("Failed to update sensors data")

  # The intent inputs state
  context = array([
    1 if State.awake else 0,
    State.on,
    len(State.prompts),
    len(State.utterances),
    State.speaking,
    normalizeCpuTemp(State.cpuTemp),
    State.ambientNoise,
    random(),
  ])
  
  debug(context, 'State context')
  
  sensors.update()
  return context

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
