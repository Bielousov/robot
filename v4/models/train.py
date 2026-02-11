import sys
import time
import numpy as np
from itertools import product
from pathlib import Path
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report

ACCURACY_TRESHOLD = 0.9

# Start the overall timer
total_start_time = time.perf_counter()

# --- INITIALIZATION ---
v4_path = Path(__file__).parent.parent.resolve()
if str(v4_path) not in sys.path:
    sys.path.insert(0, str(v4_path))

from config import Paths, ModelConfig
from lib.ModelManager import ModelManager

manager = ModelManager(Paths)

def expand_dataset(raw_data, input_keys, steps=5):
    """Generates Cartesian product and deduplicates samples."""
    unique_samples = {} # Use a dict to keep {tuple_of_inputs: label}
    
    print(f"[System] Expanding dataset", end="", flush=True)
    
    for entry in raw_data:
        prop_variants = []
        for key in input_keys:
            val = entry['inputs'][key]
            if isinstance(val, list):
                start, end = val[0], val[1]
                steps_list = [round(start + (i * (end - start) / (steps - 1)), 2) for i in range(steps)]
                prop_variants.append(steps_list)
            else:
                prop_variants.append([val])
        
        # Cartesian Product
        for combination in product(*prop_variants):
            # DEDUPLICATION: 
            # If the same input combo exists, the latest rule in JSON wins
            unique_samples[combination] = entry['label']
            
        print(".", end="", flush=True) # Progress dots for expansion
            
    X_expanded = [list(k) for k in unique_samples.keys()]
    y_expanded = list(unique_samples.values())
    
    # Rebuild verification list from unique samples
    verification_list = [
        {"description": "Unique Sample", "inputs": dict(zip(input_keys, k)), "label": v}
        for k, v in unique_samples.items()
    ]
    
    print(f" Done.")
    return np.array(X_expanded), np.array(y_expanded), verification_list


try:
    raw_data = manager._load_model("ModelTrainingData")
except Exception as e:
    print(f"[Error] Could not load training data: {e}")
    sys.exit(1)

# --- DYNAMIC KEY DETECTION ---
input_keys = list(raw_data[0]['inputs'].keys())
X, y, expanded_data = expand_dataset(raw_data, input_keys, steps=5)

print(f"[System] Deduplication complete: {len(X)} unique samples remaining.")

# --- SCALING ---
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# --- TRAINING ---
print(f"[System] Training Neural Network (this may take a moment)", end="", flush=True)
model = MLPClassifier(**ModelConfig)

# Training progress "fake" pulse because MLPClassifier.fit is blocking
# For true live progress, we'd use partial_fit, but that's overkill for this size
model.fit(X_scaled, y)
print(" Done.")

# --- DIAGNOSTICS ---
y_pred = model.predict(X_scaled)
accuracy = accuracy_score(y, y_pred)
total_end_time = time.perf_counter()
total_duration = total_end_time - total_start_time

# --- FINAL SUMMARY ---
print("\n" + "="*40)
print(f"       BRAIN TRAINING RESULTS")
print("="*40)
print(f"Overall Process Time : {total_duration:.2f} seconds")
print(f"Unique Samples       : {len(X)}")
print(f"Feature Set          : {', '.join(input_keys)}")
print(f"Epochs Run           : {model.n_iter_} / {model.max_iter}")
print(f"Loss Score           : {model.loss_:.6f}")
print(f"Training Accuracy    : {accuracy * 100:.2f}%")
print("-" * 40)

# 6. Detailed Report
target_names = ['Nothing', 'Hello', 'Goodbye', 'Prompt', 'Utterance', 'Speak']
print(classification_report(y, y_pred, labels=[0, 1, 2, 3, 4, 5], target_names=target_names, zero_division=0))

# 8. Save
if accuracy > ACCURACY_TRESHOLD:
    manager.save(model, scaler)
    print(f"\n[SUCCESS] Brain saved to {Paths.Model}") 
else:
    print("\n[WARNING] Accuracy threshold not met. Save aborted.")