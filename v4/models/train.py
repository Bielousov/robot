import sys
import time
import numpy as np
from pathlib import Path
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report

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

# --- DYNAMIC KEY DETECTION ---
input_keys = list(raw_data[0]['inputs'].keys())
print(f"[System] Detecting input features: {input_keys}")

X = []
y = []
for entry in raw_data:
    X.append([entry['inputs'][key] for key in input_keys])
    y.append(entry['label'])

X = np.array(X)
y = np.array(y)

# 3. Scale the data
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# 4. Define and Train the Model
print(f"Training the {len(input_keys)}-input brain on {len(X)} rules...")

model = MLPClassifier(**ModelConfig.BRAIN_PARAMS)

start_time = time.perf_counter()
model.fit(X_scaled, y)
end_time = time.perf_counter()

training_time = end_time - start_time

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
print(f"Input features       : {len(input_keys)}")
print(f"Epochs completed     : {epochs_run} / {max_epochs}")
print(f"Early stopping       : {'YES' if early_stopped else 'NO'}")
print(f"Final loss           : {model.loss_:.6f}")
print(f"Training time        : {training_time:.2f} seconds")
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

# 7. Safety Check: Verify Logic
def quick_test(awake_phase, prompted, speaking, time_since, tod):
    test_pt = np.array([[awake_phase, prompted, speaking, time_since, tod]])
    scaled = scaler.transform(test_pt)
    return model.predict(scaled)[0]

print("Logic Verification:")
t1 = quick_test(1, 0, 0, 10.0, 14.0)
print(f" - 2:00 PM + Idle: {'PASS' if t1 == 3 else 'FAIL'} (Predicted {target_names[t1]})")

t2 = quick_test(1, 0, 0, 10.0, 23.0)
print(f" - 11:00 PM + No Prompt: {'PASS' if t2 == 0 else 'FAIL'} (Predicted {target_names[t2]})")

t3 = quick_test(1, 1, 0, 10.0, 23.0)
print(f" - 11:00 PM + PROMPTED: {'PASS' if t3 == 3 else 'FAIL'} (Predicted {target_names[t3]})")

# 8. Save using the Manager
if accuracy > 0.9:
    manager.save(model, scaler)
    print(f"\n[SUCCESS] {len(input_keys)}-Input Brain and Scaler saved via ModelManager.")
else:
    print("\n[WARNING] Accuracy too low. Brain not saved.")
