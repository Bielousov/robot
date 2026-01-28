from numpy import random

class NeuronLayer:
  def __init__(self, numberOfNeurons, numberOfInputs):
    self.inputs = numberOfInputs
    self.neurons = numberOfNeurons
    self.weights = 2 * random.random((numberOfInputs, numberOfNeurons)) - 1
