import warnings
from numpy import absolute, array, clip, dot, exp
from .ModelLoader import loadModel, saveModel
from .NeuronLayer import NeuronLayer

warnings.filterwarnings('ignore')

class NeuralNetwork:
    def __init__(self, inputs, outputs):
        self.accuracy = 0;
        self.baseAccuracy = 0;
        self.epoch = 0
        self.baseEpoch = 0
        self.layers = []
        self.isTraining = False
        self.inputs = inputs
        self.outputs = outputs

    def __setAccuracy(self, errors):
        self.accuracy = 1 - max(absolute(array(errors).flatten()))

    # The Sigmoid function, which describes an S shaped curve.
    # We pass the weighted sum of the inputs through this function to
    # normalise them between 0 and 1.
    def __sigmoid(self, x):
        return 1 / (1 + exp(-x))

    # The derivative of the Sigmoid function.
    # This is the gradient of the Sigmoid curve.
    # It indicates how confident we are about the existing weight.
    def __sigmoid_derivative(self, x):
        return x * (1 - x)

    def addLayer(self, numberOfNeurons):
        layerInputs = self.layers[-1].neurons if len(self.layers) > 0 else self.inputs
        self.layers.append(NeuronLayer(numberOfNeurons, layerInputs))

    # We train the neural network through a process of trial and error.
    # Adjusting the synaptic weights each time.
    def train(self, trainingInputs, trainingOutputs, numberOfTrainingIterations):
        self.isTraining = True
        trainEpoch = self.epoch + numberOfTrainingIterations
        while self.epoch < trainEpoch and self.isTraining:
            self.epoch = self.epoch + 1

            # Pass the training set through our neural network
            activations = self.__getActivations(trainingInputs)

            #Calculate errors and deltas for each layer
            # (By looking at the weights in next layer 1, determine 
            # by how much layer 1 contributed to the error in layer 2).
            deltas = []
            for idx, outputs in enumerate(reversed(activations)):
                if idx == 0:
                    errors = trainingOutputs - outputs
                    self.__setAccuracy(errors)
                else:
                    errors = deltas[-1].dot(self.layers[-idx].weights.T)
                deltas.append(errors * self.__sigmoid_derivative(outputs))

            # Adjust the weights.
            inputs = trainingInputs
            for idx, layer in enumerate(self.layers):
                layer.weights += inputs.T.dot(deltas.pop())
                inputs = activations[idx]
        self.isTraining = False

    # Get neural network activations.
    def __getActivations(self, inputData):
        activations = []
        inputs = clip(inputData, 0, 1000)
        for layer in self.layers:
            outputs = self.__sigmoid(dot(inputs, layer.weights))
            activations.append(outputs)
            inputs = outputs
        return activations

    def run(self, inputData):
        activations = self.__getActivations(inputData)
        return activations[-1]

    def load(self, path):
        self.isTraining = False
        loadModel(self, path)
        self.summary()

    def save(self, path):
        self.baseAccuracy = self.accuracy
        self.baseEpoch = self.epoch
        saveModel(self, path)
    
    def summary(self):
        print("Epoch:", self.epoch, "Accuracy:", "{:.5f}".format(self.accuracy * 100), '%')