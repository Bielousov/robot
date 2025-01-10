from numpy import array, loadtxt

from NeuralNetwork import NeuralNetwork
from Threads import Process

class IntentsModel:
    def __init__(self, config):
        self._process = Process()
        self.modelPath = config.PATH
        self.trainingSetPath = config.TRAINING_DATA_PATH
        self.validationSetPath = config.VALIDATION_DATA_PATH

        self.training = False
        self.trainingEpochs = config.TRAINING_EPOCHS
        self.trainingThreshold = config.TRAINING_THRESHOLD

        self.neuralNetworkInputs = config.INPUTS
        self.neuralNetworkNeurons = [config.INPUTS, *config.LAYERS, config.OUTPUTS]
        self.neuralNetworkOutputs = config.OUTPUTS

        self.setup()
        self.initializeModel()

    def __loadTrainingSet(self):
        try:
            print("Loading training data set")
            trainingSet = loadtxt(self.trainingSetPath, delimiter=',')
            self.__trainingSetInputs = array(trainingSet[:,0:self.neuralNetworkInputs])
            self.__trainingSetOutputs = array(trainingSet[:,self.neuralNetworkInputs:self.neuralNetworkInputs + self.neuralNetworkOutputs])
        except FileNotFoundError:
            print("Training data set file not found at", self.trainingSetPath)
    
    def __loadModel(self):
        if (self.modelPath):
            self.neuralNetwork.load(self.modelPath)
    
    def __saveModel(self):
        if (self.modelPath):
            self.neuralNetwork.save(self.modelPath)

    def __initialTrain(self, accuracy = 0.6, maxEpochs = 100000):
        initialTraining=True
        while initialTraining or (self.neuralNetwork.epoch < maxEpochs and self.neuralNetwork.accuracy < accuracy):
            self.train(initialTraining)
            initialTraining=False

    def run(self, context):
        return self.neuralNetwork.run([context])

    def setup(self):
        self.neuralNetwork = NeuralNetwork(self.neuralNetworkInputs, self.neuralNetworkOutputs)
        for n in self.neuralNetworkNeurons:
            self.neuralNetwork.addLayer(n)

        self.__loadTrainingSet()
        self.__loadModel()

    def initializeModel(self):
        self.__initialTrain(accuracy=self.trainingThreshold)
        self.neuralNetwork.summary()
        self.validate()

    def _train(self, forceSave):
        self.isTraining = True
        self.neuralNetwork.train(
            self.__trainingSetInputs,
            self.__trainingSetOutputs,
            self.trainingEpochs
        )
        self.neuralNetwork.summary()

        if self.neuralNetwork.accuracy > self.trainingThreshold and (round(self.neuralNetwork.accuracy, 4) > round(self.neuralNetwork.baseAccuracy, 4) or forceSave):
            self.__saveModel()
            self.isTraining = True
            return True
        
        self.isTraining = True
        return False

    def train(self, forceSave=False):
        if self.training:
            return
        
        self._process.run(self._train, forceSave)

    def validate(self):
        if not hasattr(self, '__validationSet'):
            print("Loading validation data from", self.validationSetPath)
            self.__validationSet = loadtxt(self.validationSetPath, delimiter=',')
        print("Validating model with data:\n", self.__validationSet)
        validationResults = self.run(self.__validationSet)
        print("Validating results:\n", validationResults)