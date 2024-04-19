from config import Config
from classes.Benchmark import Benchmark
from classes.Decisions import Decisions

testTrainingPerformance = Benchmark()

decisions = Decisions(
    modelPath = Config.MODEL_PATH,
    trainingSetPath = Config.MODEL_DATA_PATH,
    validationSetPath = Config.MODEL_DATA_VALIDATION_PATH,
    trainingEpochs = 1000,
)

decisions.setup()

while True:
    testTrainingPerformance.start()
    decisions.train()
    testTrainingPerformance.end()