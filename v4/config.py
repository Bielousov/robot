from dotenv import load_dotenv
from os import getenv, path
from sklearn.neural_network import MLPClassifier

from lib.Enum import Enum

load_dotenv()

Env = Enum (
  BrainConfidenceScore  = float(getenv('BRAIN_CONFIDENCE_THRESHOLD')),
  BrainFrequency        = int(getenv('BRAIN_FREQUENCY')),
  Debug                 = bool(int(getenv('DEBUG'))),
  Voice                 = getenv('VOICE'),
  VoiceSampleRate       = int(getenv('VOICE_SAMPLE_RATE')),
)

# --- Model Instance Setup ---
BASE_DIR = path.dirname(path.abspath(__file__))

Paths = Enum (
  Dictionary = path.join(BASE_DIR, "dictionary/en.json"),
  Model = path.join(BASE_DIR, "models/robot_model.pkg"),
  ModelScaler = path.join(BASE_DIR, "models/scaler.pkg"),
  ModelTrainingData = path.join(BASE_DIR, "models/training_data.json")
)

ModelConfig = {
    'hidden_layer_sizes': (16, 16),
    'max_iter': 100_000,
    'activation': 'relu',
    'solver': 'adam',
    'alpha': 0,
    'random_state': 42
}