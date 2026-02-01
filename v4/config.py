from dotenv import load_dotenv
from os import getenv, path

from lib.Enum import Enum

load_dotenv()

Env = Enum (
  Voice             = getenv('VOICE'),
  VoiceSampleRate = int(getenv('VOICE_SAMPLE_RATE')),
)
