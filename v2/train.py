from config import ModelConfig
from lib.Benchmark import Benchmark
from lib.Decisions import Decisions

testTrainingPerformance = Benchmark()

decisions = Decisions(
    modelPath = ModelConfig.MODEL_PATH,
    trainingSetPath = ModelConfig.MODEL_DATA_PATH,
    validationSetPath = ModelConfig.MODEL_DATA_VALIDATION_PATH,
    trainingEpochs = 1000,
)

decisions.setup()

while True:
    testTrainingPerformance.start()
    decisions.train()
    testTrainingPerformance.end()