import sys
import numpy as np
from pathlib import Path
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report

# Path Setup
v4_path = Path(__file__).parent.parent.parent.resolve()
if str(v4_path) not in sys.path:
    sys.path.insert(0, str(v4_path))
    
# Import your new configuration tools
from config import Paths
from lib.ModelManager import ModelManager # Assuming ModelManager is in lib/

# 1. Initialize the Manager
# We pass the Paths class so it knows where to find everything
manager = ModelManager(Paths)

# 2. Load Data using the Manager
try:
    # Use the generic _load_model method which detects .json automatically
    raw_data = manager._load_model("ModelTrainingData")
except Exception as e:
    print(f"[Error] Could not load training data: {e}")
    sys.exit(1)

X = []
y = []
for entry in raw_data:
    inputs = entry['inputs']
    X.append([
        inputs['awake'], 
        inputs['prompted'], 
        inputs['time_since_spoke'], 
        inputs['tod']
    ])
    y.append(entry['label'])

X = np.array(X)
y = np.array(y)

# 3. Scale the data
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# 4. Define and Train the Model
print(f"Training the 4-input brain on {len(X)} rules...")
model = MLPClassifier(
    hidden_layer_sizes=(16, 16),
    max_iter=20_000,
    activation='relu',           
    solver='lbfgs',              
    alpha=0,                     
    random_state=42
)

model.fit(X_scaled, y)

# 5. Diagnostic
y_pred = model.predict(X_scaled)
accuracy = accuracy_score(y, y_pred)

print("-" * 30)
print(f"TRAINING COMPLETE")
print(f"Rule Adherence: {accuracy * 100:.2f}%")
print("-" * 30)

# 6. Detailed Report
target_names = ['Nothing', 'Hello', 'Goodbye', 'Fact']
print(classification_report(
    y, y_pred, labels=[0, 1, 2, 3], 
    target_names=target_names, zero_division=0 
))

# 7. Safety Check: Verify 4-Input Logic
test_points = np.array([
    [1, 0, 10.0, 14.0], 
    [1, 0, 10.0, 23.0],
    [1, 1, 10.0, 23.0] 
])
test_scaled = scaler.transform(test_points)
test_preds = model.predict(test_scaled)

print("Logic Verification:")
print(f" - 2:00 PM + No Prompt: {'PASS' if test_preds[0] == 3 else 'FAIL'} (Predicted {target_names[test_preds[0]]})")
print(f" - 11:00 PM + No Prompt: {'PASS' if test_preds[1] == 0 else 'FAIL'} (Predicted {target_names[test_preds[1]]})")
print(f" - 11:00 PM + PROMPTED: {'PASS' if test_preds[2] == 3 else 'FAIL'} (Predicted {target_names[test_preds[2]]})")

# 8. Save using the Manager
# The Manager handles os.path.join and joblib.dump internally
if accuracy > 0.9:
    manager.save(model, scaler)
    print("\n[SUCCESS] 4-Input Brain and Scaler saved via ModelManager.")
else:
    print("\n[WARNING] Accuracy too low. Brain not saved.")