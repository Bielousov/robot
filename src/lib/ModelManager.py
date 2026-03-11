import os
import json
import joblib

class ModelManager:
    """
    A generic loader/saver for JSON and PKG files.
    Caches the model and scaler internally for easy access.
    """
    def __init__(self, paths, load=False):
        # paths should be a dictionary or object with .get()
        self.paths = paths
        self.model = None
        self.scaler = None

        if load:
            self.load()

    def _load_model(self, key):
        """Generic loader for a single file key."""
        # Handle if paths is a dict or an object
        path = self.paths.get(key) if hasattr(self.paths, 'get') else getattr(self.paths, key, None)
        
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
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def load(self, model_key="Model", scaler_key="ModelScaler"):
        """Loads and stores the model/scaler to self."""
        self.model = self._load_model(model_key)
        self.scaler = self._load_model(scaler_key)
        return self.model, self.scaler

    def save(self, model, scaler, model_key="Model", scaler_key="ModelScaler"):
        """Persists and updates the internal references."""
        model_path = self.paths.get(model_key) if hasattr(self.paths, 'get') else getattr(self.paths, model_key)
        scaler_path = self.paths.get(scaler_key) if hasattr(self.paths, 'get') else getattr(self.paths, scaler_key)
        
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        
        joblib.dump(model, model_path)
        joblib.dump(scaler, scaler_path)
        
        self.model = model
        self.scaler = scaler
        print(f"[Success] Model saved to: {model_path}")