from dotenv import load_dotenv
from os import getenv, path
from lib.Enum import Enum

load_dotenv()

ENV = Enum (
  CHAT_FPS                = int(getenv('CHAT_FPS')),
  DECISION_FPS            = int(getenv('DECISIONS_FPS')),
  EYES_FPS                = int(getenv('EYES_FPS')),
  VOICE_FPS               = int(getenv('VOICE_FPS')),
  VOICE_FRAMES_PER_BUFFER = int(getenv('VOICE_FRAMES_PER_BUFFER')),
  VOICE_SAMPLE_RATE       = int(getenv('VOICE_SAMPLE_RATE')),
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
  PERSONALITY = f"You are a robot called {ENV.NAME}. You are self-centered, narcissistic, sarcastic and impersonate Bender from Futurama and use his catchphrases occasionally. If asked about yourself, you include your name in your response, but keep it under 30 words.",
  TTS_FORMAT = getenv('OPEN_AI_TTS_FORMAT'),
  TTS_FRAMES_PER_BUFFER = getenv('VOICE_FRAMES_PER_BUFFER'),
  TTS_MODEL = getenv('OPEN_AI_TTS_MODEL'),
  TTS_VOICE = getenv('OPEN_AI_TTS_VOICE'),
)