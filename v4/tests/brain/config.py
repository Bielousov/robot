import sys
from dotenv import load_dotenv
from os import getenv, path
from pathlib import Path
from sklearn.neural_network import MLPClassifier

from lib.Enum import Enum

load_dotenv()

Env = Enum (
  Voice             = getenv('VOICE'),
  VoiceSampleRate = int(getenv('VOICE_SAMPLE_RATE')),
)

# --- Model Instance Setup ---
BASE_DIR = path.dirname(path.abspath(__file__))

Paths = Enum (
  Dictionary = path.join(BASE_DIR, "dictionary.json"),
  Model = path.join(BASE_DIR, "models/robot_model.pkg"),
  ModelScaler = path.join(BASE_DIR, "models/scaler.pkg"),
  ModelTrainingData = path.join(BASE_DIR, "models/training_data.json")
)

Model = MLPClassifier(
    hidden_layer_sizes=(16, 16),
    max_iter=20_000,
    activation='relu',           
    solver='lbfgs',              
    alpha=0,                     
    random_state=42
)
