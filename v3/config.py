from dotenv import load_dotenv
from os import getenv
from lib.Enum import Enum

load_dotenv()

ENV = Enum (
  CHAT_FPS                = int(getenv('CHAT_FPS')),
  EYES_FPS                = int(getenv('EYES_FPS')),
  NAME                    = getenv('NAME'),
)

OPEN_AI = Enum (
  MODEL = getenv('OPEN_AI_MODEL'),
  MODEL_TTS = getenv('OPEN_AI_TTS_MODEL'),
  PERSONALITY = f"You are a robot called {ENV.NAME}. You are self-centered, narcissistic, sarcastic and impersonate Bender from Futurama and use his catchphrases occasionally. If asked about yourself, you include your name in your response, but keep it under 30 words.",
  VOICE = getenv('OPEN_AI_TTS_VOICE'),
)