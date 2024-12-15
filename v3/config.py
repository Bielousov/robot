import os
from dotenv import load_dotenv
from lib.Enum import Enum

load_dotenv()

ENV = Enum (
  DECISION_FPS            = int(os.getenv('DECISIONS_FPS')),
  EYES_FPS                = int(os.getenv('EYES_FPS')),
  INTENTS_FPS             = int(os.getenv('INTENTS_FPS')),
  INTENTS_THRESHOLD       = float(os.getenv('INTENTS_THRESHOLD')),
  NAME                    = os.getenv('NAME'),
  PYTHON                  = "python3",
  TRAINING_EPOCHS         = int(os.getenv('TRAINING_EPOCHS')),
)

ModelConfig = Enum (
  INPUTS = 5,
  LAYERS = [30],
  OUTPUTS = 6,
  TRAIN_THRESHOLD = 0.6,

  MODEL_DATA_PATH = os.path.join(os.path.dirname(__file__), 'models/data/decisions-training.csv'),
  MODEL_DATA_VALIDATION_PATH = os.path.join(os.path.dirname(__file__), 'models/data/decisions-validation.csv'),
  MODEL_PATH = os.path.join(os.path.dirname(__file__), 'models/build/decisions.model.npy'),

  MODEL_OUTPUT_ANNOTATION = [
    'wakeup',
    'train',
    'blink',
    'alert',
    'anger',
    'joy'
  ]
)
