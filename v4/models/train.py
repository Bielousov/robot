import sys
import time
import numpy as np
from itertools import product
from pathlib import Path
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report

ACCURACY_TRESHOLD = 0.9

def expand_dataset(raw_data, input_keys, steps=5):
    X_expanded = []
    y_expanded = []
    verification_list = []
    
    for entry in raw_data:
        # 1. Generate the possible values for every single key
        prop_variants = []
        
        for key in input_keys:
            val = entry['inputs'][key]
            if isinstance(val, list):
                # Create a list of 5 linear steps for this specific prop
                start, end = val[0], val[1]
                steps_list = [round(start + (i * (end - start) / (steps - 1)), 2) for i in range(steps)]
                prop_variants.append(steps_list)
            else:
                # Just a single value in a list for the product function
                prop_variants.append([val])
        
        # 2. Generate the Cartesian Product (all combinations)
        # e.g., 5 chaos * 5 time_since_spoke * 5 tod = 125 combinations
        for combination in product(*prop_variants):
            # 'combination' is a tuple of values in the order of input_keys
            X_expanded.append(list(combination))
            y_expanded.append(entry['label'])
            
            # Map back to dict for the verification list
            row_inputs = dict(zip(input_keys, combination))
            verification_list.append({
                "description": f"{entry['description']} (Combo)",
                "inputs": row_inputs,
                "label": entry['label']
            })
            
    return np.array(X_expanded), np.array(y_expanded), verification_list

# Fix paths
v4_path = Path(__file__).parent.parent.resolve()
if str(v4_path) not in sys.path:
    sys.path.insert(0, str(v4_path))

from config import Paths, ModelConfig
from lib.ModelManager import ModelManager

# 1. Initialize the Manager
manager = ModelManager(Paths)

# 2. Load Data
try:
    raw_data = manager._load_model("ModelTrainingData")
except Exception as e:
    print(f"[Error] Could not load training data: {e}")
    sys.exit(1)

if not raw_data:
    print("[Error] Training data is empty.")
    sys.exit(1)

# --- DYNAMIC KEY DETECTION & DATA EXPANSION ---
input_keys = list(raw_data[0]['inputs'].keys())
print(f"[System] Detecting input features: {input_keys}")


# Expand ranges (e.g., [0.0, 1.0] -> 5 rows)
X, y, expanded_data = expand_dataset(raw_data, input_keys, steps=5)

print(f"Dataset expanded: {len(raw_data)} rules -> {len(X)} training samples.")

# 3. Scale the data
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# 4. Define and Train the Model
print(f"Training the {len(input_keys)}-input brain on {len(X)} rules...")

model = MLPClassifier(**ModelConfig)

start_time = time.perf_counter()
model.fit(X_scaled, y)
training_time = time.perf_counter() - start_time

# 5. Diagnostic
y_pred = model.predict(X_scaled)
accuracy = accuracy_score(y, y_pred)

# --- TRAINING SUMMARY ---
epochs_run = model.n_iter_
max_epochs = model.max_iter
early_stopped = epochs_run < max_epochs

print("-" * 40)
print("TRAINING COMPLETE")
print(f"Rules trained on     : {len(X)}")
print(f"Input features       : {len(input_keys)} ({', '.join(input_keys)})")
print(f"Epochs completed     : {epochs_run} / {max_epochs}")
print(f"Final loss           : {model.loss_:.6f}")
print(f"Rule adherence       : {accuracy * 100:.2f}%")
print("-" * 40)

# 6. Detailed Report
target_names = ['Nothing', 'Hello', 'Goodbye', 'Fact']
print(classification_report(
    y, y_pred,
    labels=[0, 1, 2, 3],
    target_names=target_names,
    zero_division=0
))

# 7. DYNAMIC LOGIC VERIFICATION
# Instead of hardcoding 5 params, we use the model's own logic
def verify_rules(data, model, scaler, keys, limit=5):
    print("Logic Verification (Sampling first few rules):")
    success_count = 0
    samples = data[:limit]
    
    for entry in samples:
        # Build the feature vector based on dynamic keys
        test_pt = np.array([[entry['inputs'][k] for k in keys]])
        scaled = scaler.transform(test_pt)
        prediction = model.predict(scaled)[0]
        
        status = "PASS" if prediction == entry['label'] else "FAIL"
        if status == "PASS": success_count += 1
        
        print(f" - {entry['description'][:30]:<30}: {status} (Wanted {entry['label']}, got {prediction})")
    
    return success_count

verify_rules(expanded_data, model, scaler, input_keys)

# 8. Save using the Manager
if accuracy > ACCURACY_TRESHOLD:
    manager.save(model, scaler)
    print(f"\n[SUCCESS] {len(input_keys)}-Input Brain and Scaler saved via ModelManager.")
else:
    print("\n[WARNING] Accuracy too low. Brain not saved.")
