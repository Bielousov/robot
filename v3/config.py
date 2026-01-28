from dotenv import load_dotenv
from os import getenv, path
from lib.Enum import Enum

load_dotenv()

ENV = Enum (
  DEBUG                   = bool(int(getenv('DEBUG'))),
  INTENT_FPS              = int(getenv('INTENT_FPS')),
  EYES_FPS                = int(getenv('EYES_FPS')),
  NAME                    = getenv('NAME'),
  VOICE                   = getenv('VOICE'),
)


MODEL = Enum (
  TRAINING_EPOCHS         = int(getenv('TRAINING_EPOCHS')),
  INPUTS                  = int(getenv('INTENT_MODEL_INPUTS')),
  OUTPUTS                 = int(getenv('INTENT_MODEL_OUTPUTS')),
  LAYERS                  = int(getenv('INTENT_MODEL_LAYERS')),
  VERSION                 = int(getenv('INTENT_MODEL_VERSION')),
  TRAINING_THRESHOLD      = float(getenv('TRAINING_THRESHOLD')),

  TRAINING_DATA_PATH = path.join(path.dirname(__file__), 'models/data/intents-training.csv'),
  VALIDATION_DATA_PATH = path.join(path.dirname(__file__), 'models/data/intents-validation.csv'),

  INTENT_THRESHOLD   = float(getenv('INTENT_THRESHOLD')),
  INTENT_ANNOTATION = [
    'wakeup',
    'ask',
    'blink',
    'say',
    'scared',
    'bored',
    'train',
    'wonder'
  ]
)

OPEN_AI = Enum (
  CACHE_LIMIT = int(getenv('OPEN_AI_CACHE_LIMIT')),
  MODEL = getenv('OPEN_AI_MODEL'),
  PERSONALITY = f"You are a robot called {ENV.NAME}. You are sarcastic and impersonate Bender from Futurama, use his catchphrases occasionally and swear a lot. If asked about yourself, you include your name in your response, but keep it under 30 words.",
  TTS_ENABBLED=bool(int(getenv('OPEN_AI_TTS'))),
  TTS_FORMAT = getenv('OPEN_AI_TTS_FORMAT'),
  TTS_FRAMES_PER_BUFFER = int(getenv('OPEN_AI_TTS_FRAMES_PER_BUFFER')),
  TTS_MODEL = getenv('OPEN_AI_TTS_MODEL'),
  TTS_SAMPLE_RATE = int(getenv('OPEN_AI_TTS_SAMPLE_RATE')),
  TTS_VOICE = getenv('OPEN_AI_TTS_VOICE'),
)