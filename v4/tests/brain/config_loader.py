import joblib
import json
import os

def load_brain(paths):
    """
    Loads the neural network model and the scaler for input normalization.
    Expects an object/class with .Model and .ModelScaler attributes.
    """
    # Use .Model and .ModelScaler to match your config.Paths class
    model_path = paths.Model
    scaler_path = paths.ModelScaler

    print(f"[Loader] Checking paths:\n - {model_path}\n - {scaler_path}")

    if not os.path.exists(model_path) or not os.path.exists(scaler_path):
        raise FileNotFoundError(
            f"Brain files (.pkg) not found.\n"
            f"Target: {model_path}"
        )

    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)
    
    return model, scaler

def load_json(path):
    """
    Loads JSON from a direct absolute file path.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"JSON file not found: {path}")

    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        raise Exception(f"load_json error: {e}")