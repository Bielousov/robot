from dotenv import load_dotenv
from os import getenv, path

from v4.lib.Enum import Enum

load_dotenv()

ENV = Enum (
  VOICE = getenv('VOICE'),
)
