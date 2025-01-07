from dotenv import load_dotenv
from os import getenv, path
from lib.Enum import Enum

load_dotenv()

ENV = Enum (
  INTENT_FPS              = int(getenv('INTENT_FPS')),
  EYES_FPS                = int(getenv('EYES_FPS')),
  NAME                    = getenv('NAME'),
  VOICE                   = getenv('VOICE'),
)

MODEL = Enum (
  INPUTS = 3,
  LAYERS = [30],
  OUTPUTS = 6,
  INTENT_THRESHOLD   = float(getenv('INTENT_THRESHOLD')),
  TRAINING_EPOCHS     = int(getenv('TRAINING_EPOCHS')),
  TRAINING_THRESHOLD     = float(getenv('TRAINING_THRESHOLD')),

  DATA_PATH = path.join(path.dirname(__file__), 'models/data/decisions-training.csv'),
  DATA_VALIDATION_PATH = path.join(path.dirname(__file__), 'models/data/decisions-validation.csv'),
  PATH = path.join(path.dirname(__file__), 'models/build/decisions.model.npy'),

  OUTPUT_ANNOTATION = [
    'wakeup',
    'ask',
    'blink',
    'say',
    'train',
    'wonder'
  ]
)

OPEN_AI = Enum (
  MODEL = getenv('OPEN_AI_MODEL'),
  PERSONALITY = f"You are a robot called {ENV.NAME}. You are self-centered, narcissistic, sarcastic and impersonate Bender from Futurama and use his catchphrases occasionally. If asked about yourself, you include your name in your response, but keep it under 30 words.",
  TTS_ENABBLED=bool(int(getenv('OPEN_AI_TTS'))),
  TTS_FORMAT = getenv('OPEN_AI_TTS_FORMAT'),
  TTS_FRAMES_PER_BUFFER = int(getenv('OPEN_AI_TTS_FRAMES_PER_BUFFER')),
  TTS_MODEL = getenv('OPEN_AI_TTS_MODEL'),
  TTS_SAMPLE_RATE = int(getenv('OPEN_AI_TTS_SAMPLE_RATE')),
  TTS_VOICE = getenv('OPEN_AI_TTS_VOICE'),
)