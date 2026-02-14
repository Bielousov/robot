from dotenv import load_dotenv
from os import getenv, path
from sklearn.neural_network import MLPClassifier

from lib.Enum import Enum

load_dotenv()

Name = getenv('NAME')

Env = Enum (
  BrainConfidenceScore  = float(getenv('BRAIN_CONFIDENCE_THRESHOLD', '0.9')),
  BrainFrequencyDelta   = int(getenv('BRAIN_FREQUENCY_DELTA', '1')),
  BrainFrequencyGamma   = int(getenv('BRAIN_FREQUENCY_GAMMA', '20')),
  Debug                 = bool(int(getenv('DEBUG', '0'))),
  Voice                 = getenv('PIPER_MODEL_NAME', 'en_US-danny-low'),
  VoiceSampleRate       = int(getenv('PIPER_SAMPLE_RATE', '16000')),
  VoskModel             = getenv('VOSK_MODEL_NAME'),
  VoskSampleRate        = int(getenv('VOSK_SAMPLE_RATE', '16000')),
  VoskSynonyms          = getenv('VOSK_SYNONYMS', 'robot').split(',')
)

# --- Model Instance Setup ---
BASE_DIR = path.dirname(path.abspath(__file__))

Paths = Enum (
  Model = path.join(BASE_DIR, "models/robot_model.pkg"),
  ModelScaler = path.join(BASE_DIR, "models/scaler.pkg"),
  ModelTrainingData = path.join(BASE_DIR, "models/training_data.json"),
  Prompts = path.join(BASE_DIR, "dictionary/prompts.json")
)

ModelConfig = {
    'hidden_layer_sizes': (16, 16),
    'max_iter': 100_000,
    'activation': 'relu',
    'solver': 'adam',
    'alpha': 0.01,
}