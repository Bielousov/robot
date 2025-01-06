from dotenv import load_dotenv
from os import getenv, path
from lib.Enum import Enum

load_dotenv()

ENV = Enum (
  CHAT_FPS                = int(getenv('CHAT_FPS')),
  DECISION_FPS            = int(getenv('DECISIONS_FPS')),
  EYES_FPS                = int(getenv('EYES_FPS')),
  NAME                    = getenv('NAME'),
)

DecisionModelConfig = Enum (
  INPUTS = 3,
  LAYERS = [30],
  OUTPUTS = 6,
  TRAIN_THRESHOLD = 0.6,

  MODEL_DATA_PATH = path.join(path.dirname(__file__), 'models/data/decisions-training.csv'),
  MODEL_DATA_VALIDATION_PATH = path.join(path.dirname(__file__), 'models/data/decisions-validation.csv'),
  MODEL_PATH = path.join(path.dirname(__file__), 'models/build/decisions.model.npy'),

  MODEL_OUTPUT_ANNOTATION = [
    'wakeup',
    'train',
    'blink',
  ]
)

OPEN_AI = Enum (
  MODEL = getenv('OPEN_AI_MODEL'),
  MODEL_TTS = getenv('OPEN_AI_TTS_MODEL'),
  PERSONALITY = f"You are a robot called {ENV.NAME}. You are self-centered, narcissistic, sarcastic and impersonate Bender from Futurama and use his catchphrases occasionally. If asked about yourself, you include your name in your response, but keep it under 30 words.",
  VOICE = getenv('OPEN_AI_TTS_VOICE'),
)