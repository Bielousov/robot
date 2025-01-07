from config import MODEL
from copy import deepcopy
from lib.Benchmark import Benchmark
from lib.IntentsModel import IntentsModel

testTrainingPerformance = Benchmark()

modelConfig = deepcopy(MODEL)
modelConfig.TRAINING_EPOCHS = 1000

intentsModel = IntentsModel(modelConfig)

while True:
    testTrainingPerformance.start()
    intentsModel.train()
    testTrainingPerformance.end()