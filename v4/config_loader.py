import os
import json
import joblib

# Determine the absolute path to the directory where this file lives
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Ensure these keys match exactly what you call in train.py and main.py
PATHS = {
    "dictionary": os.path.join(BASE_DIR, "dictionary.json"),
    "model": os.path.join(BASE_DIR, "models/robot_model.pkg"),
    "scaler": os.path.join(BASE_DIR, "models/scaler.pkg"),
    "training_data": os.path.join(BASE_DIR, "models/training_data.json"),
}

def load_json(key):
    path = PATHS.get(key)
    if path is None:
        raise ValueError(f"Key '{key}' not found in PATHS dictionary!")
    if not os.path.exists(path):
        raise FileNotFoundError(f"File missing at: {path}")
    with open(path, 'r') as f:
        return json.load(f)

def load_brain():
    model_path = PATHS.get("model")
    scaler_path = PATHS.get("scaler")
    
    # Check if paths are actually defined
    if not model_path or not scaler_path:
        raise ValueError("Model or Scaler path is undefined in config_loader.py")
        
    if not os.path.exists(model_path) or not os.path.exists(scaler_path):
        raise FileNotFoundError("Brain files (.pkg) not found. Run train_model.py first!")
        
    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)
    return model, scaler

def save_brain(model, scaler):
    joblib.dump(model, PATHS["model"])
    joblib.dump(scaler, PATHS["scaler"])