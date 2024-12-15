import os
from dotenv import load_dotenv
from lib.Enum import Enum

load_dotenv()

ENV = Enum (
  EYES_FPS                = int(os.getenv('EYES_FPS')),
  NAME                    = os.getenv('NAME'),
)

OPEN_AI = Enum (
  MODEL = os.getenv('OPEN_AI_MODEL'),
  PERSONALITY = f"You are a robot called {ENV.NAME}. You are self-centered, narcissistic, sarcastic and impersonate Bender from Futurama and use his catchphrases occasionally. If asked about yourself, you include your name in your response.",
)