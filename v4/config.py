from dotenv import load_dotenv
from os import getenv, path

from lib.Enum import Enum

load_dotenv()

ENV = Enum (
  VOICE = getenv('VOICE'),
)
