import threading, time
from copy import deepcopy

from ..config import MODEL
from lib.Benchmark import Benchmark
from lib.IntentsModel import IntentsModel

TRAINING_EPOCHS = 10_000

# --- internal stop flag ---
_stop_event = threading.Event()
_start_time = None

def stop():
    """Request graceful shutdown."""
    _stop_event.set()

def get_runtime_seconds():
    if _start_time is None:
        return 0
    return time.time() - _start_time

def run():
    global _start_time
    _start_time = time.time()

    testTrainingPerformance = Benchmark()

    modelConfig = deepcopy(MODEL)
    modelConfig.TRAINING_EPOCHS = TRAINING_EPOCHS

    intentsModel = IntentsModel(modelConfig)

    print("[train] Started training loop")

    try:
        while not _stop_event.is_set():
            # Run ONE training cycle
            testTrainingPerformance.start()
            intentsModel.train(False)
            testTrainingPerformance.end()

            # Give signal handling a chance
            time.sleep(0)

    finally:
        print("[train] Cleaning up…")
        if hasattr(intentsModel, "stop"):
            intentsModel.isTraining = False
            intentsModel.saveModel()
            intentsModel.info()
            intentsModel.validate()
            time.sleep(1)

