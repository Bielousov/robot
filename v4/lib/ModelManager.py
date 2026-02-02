import os
import json
import joblib

class ModelManager:
    """
    A generic loader for JSON and PKG files.
    Caches the model and scaler internally for easy access.
    """
    def __init__(self, paths, load = False):
        self.paths = paths
        # Exposed attributes for the consumer
        self.model = None
        self.scaler = None

        if (load == True):
            self.load()

    def _load_model(self, key):
        """Generic loader for a single file key."""
        path = self.paths.get(key)
        
        if not path:
            raise ValueError(f"Key '{key}' not found in provided paths!")
        
        if not os.path.exists(path):
            raise FileNotFoundError(f"File missing at: {path}")

        if path.endswith('.json'):
            return self._load_json(path)
        elif path.endswith('.pkg'):
            return joblib.load(path)
        else:
            raise TypeError(f"Unsupported file format for: {path}")

    def _load_json(self, path):
        with open(path, 'r') as f:
            return json.load(f)

    def load(self, model_key="model", scaler_key="scaler"):
        """
        Loads and stores the model/scaler to self.
        Returns them for immediate unpacking if needed.
        """
        self.model = self.load(model_key)
        self.scaler = self.load(scaler_key)
        return self.model, self.scaler

    def save(self, model, scaler, model_key="model", scaler_key="scaler"):
        """Persists and updates the internal references."""
        model_path = self.paths.get(model_key)
        scaler_path = self.paths.get(scaler_key)
        
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        
        joblib.dump(model, model_path)
        joblib.dump(scaler, scaler_path)
        
        # Keep internal state in sync with saved files
        self.model = model
        self.scaler = scaler

