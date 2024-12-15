import os
from dotenv import load_dotenv
from lib.Enum import Enum

load_dotenv()

ENV = Enum (
  EYES_FPS                = int(os.getenv('EYES_FPS')),
  NAME                    = os.getenv('NAME'),
)
