from dotenv import load_dotenv
from os import getenv, path

from lib.Enum import Enum

load_dotenv()

BASE_DIR = path.dirname(path.abspath(__file__))

Name = getenv('NAME')

Env = Enum (
  BrainConfidenceScore      = float(getenv('BRAIN_CONFIDENCE_THRESHOLD', '0.9')),
  BrainContextLimit         = int(getenv('CONVERSATION_HISTORY_LIMIT', '4')),
  BrainFrequencyDelta       = int(getenv('BRAIN_FREQUENCY_DELTA', '1')),
  BrainFrequencyGamma       = int(getenv('BRAIN_FREQUENCY_GAMMA', '20')),
  Debug                     = bool(int(getenv('DEBUG', '0'))),
  EavesdropHistoryLimit     = int(getenv('EAVESDROP_HISTORY_LIMIT', '8')),
  Voice                     = getenv('PIPER_MODEL_NAME', 'en_US-danny-low'),
  VoiceSampleRate           = int(getenv('PIPER_SAMPLE_RATE', '16000')),
  WhisperWakeAliases        = getenv('WHISPER_WAKE_ALIASES', 'robot'),
  WhisperModel              = getenv('WHISPER_MODEL_HEF'),
  WhisperSampleRate         = int(getenv('WHISPER_SAMPLE_RATE', '16000')),
)

# --- Model Instance Setup ---
Paths = Enum (
  Model = path.join(BASE_DIR, "models/robot/build/classifier_model.pkg"),
  ModelScaler = path.join(BASE_DIR, "models/robot/build/classifier_scaler.pkg"),
  ModelTrainingData = path.join(BASE_DIR, "models/robot/training/data/classifier_training_data.json"),

  UtteranceModel = path.join(BASE_DIR, "models/robot/build/utterance_model.pkg"),
  UtteranceModelScaler = path.join(BASE_DIR, "models/robot/build/utterance_scaler.pkg"),
  UtteranceTrainingData = path.join(BASE_DIR, "models/robot/training/data/utterance_training_data.json"),

  Matches = path.join(BASE_DIR, "dictionary/matches.json"),
  Prompts = path.join(BASE_DIR, "dictionary/prompts.json"),
  Responses = path.join(BASE_DIR, "dictionary/responses.json")
)

ModelConfig = {
    'hidden_layer_sizes': (16, 16),
    'max_iter': 100_000,
    'activation': 'relu',
    'solver': 'adam',
    'alpha': 0.01,
}

# 2-input (eavesdropped_context, time_since_heard) -> 1-output (confidence)
# regressor - a smooth surface (a rising-then-fading hump in time_since_heard,
# scaled by an eavesdropped_context multiplier), still much simpler to fit
# than the Robot Model's classification. The absolute floors
# (MIN_CONTEXT/MIN_SILENCE_S in Utterances) stay hard gates in code rather
# than model inputs - they're step conditions, and MLPs are bad at hard
# steps (same lesson as the Robot Model's own removed `chaos` feature).
# (32, 32) here (vs (16, 16) for the single-ramp version) because the hump
# shape has more corners to trace; verified empirically to reliably clear
# train_utterance.py's R2/MSE thresholds even with as few as 8 restarts.
UtteranceModelConfig = {
    'hidden_layer_sizes': (32, 32),
    'max_iter': 100_000,
    'activation': 'relu',
    'solver': 'adam',
    'alpha': 0.00001,
}