from numpy import array, loadtxt

from .NeuralNetwork import NeuralNetwork

class IntentsModel:
    def __init__(self, config):
        self.modelPath = config.PATH
        self.trainingSetPath = config.TRAINING_DATA_PATH
        self.validationSetPath = config.VALIDATION_DATA_PATH

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
        while (self.neuralNetwork.epoch < maxEpochs and self.neuralNetwork.accuracy < accuracy):
            self.train()

    def run(self, context):
        return self.neuralNetwork.run([context])

    def setup(self):
        self.neuralNetwork = NeuralNetwork(self.neuralNetworkInputs, self.neuralNetworkOutputs)
        for n in self.neuralNetworkNeurons:
            self.neuralNetwork.addLayer(n)

        self.__loadTrainingSet()
        self.__loadModel()
        self.neuralNetwork.summary()

    def initializeModel(self):
        self.__initialTrain(accuracy=self.trainingThreshold)
        self.neuralNetwork.summary()
        self.validate()

    def train(self):
        self.neuralNetwork.train(
            self.__trainingSetInputs,
            self.__trainingSetOutputs,
            self.trainingEpochs
        )
        self.neuralNetwork.summary()

        if self.neuralNetwork.accuracy > self.trainingThreshold and self.neuralNetwork.accuracy > self.neuralNetwork.baseAccuracy:
            self.__saveModel()
            return True
        else:
            return False

    def validate(self):
        if not hasattr(self, '__validationSet'):
            print("Loading validation data from", self.validationSetPath)
            self.__validationSet = loadtxt(self.validationSetPath, delimiter=',')
        print("Validating model with data:\n", self.__validationSet)
        validationResults = self.run(self.__validationSet)
        print("Validating results:\n", validationResults)