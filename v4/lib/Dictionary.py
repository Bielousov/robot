import json
import random
import os

class Dictionary:
    """Handles loading and random selection of phrases from a JSON dictionary."""
    def __init__(self, path):
        self.path = path
        self.data = self._load()

    def _load(self):
        """Internal method to load the JSON file."""
        if not os.path.exists(self.path):
            raise FileNotFoundError(f"Dictionary file not found at: {self.path}")
        
        with open(self.path, 'r') as f:
            return json.load(f)

    def has(self, key: str) -> bool:
        """Check if a top-level key exists in the dictionary."""
        return key in self.data

    def pick(self, key, default="..."):
        """Selects a random entry from a list identified by the key."""
        
        entries = self.data.get(key)
        
        if not entries:
            return default
            
        if isinstance(entries, list):
            return random.choice(entries)
        
        # If it's a single string instead of a list, just return it
        return str(entries)

    def reload(self):
        """Refresh the dictionary data from disk without restarting."""
        self.data = self._load()
        print(f"[System] Dictionary reloaded from {self.path}")