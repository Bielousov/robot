import numpy as np
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report

from config import Paths
import config_loader 

# 1. Load Data
try:
    raw_data = config_loader.load_json(Paths.ModelTrainingData)
except FileNotFoundError as e:
    print(e)
    exit()

X = []
y = []
for entry in raw_data:
    inputs = entry['inputs']
    # input features
    X.append([
        inputs['awake'], 
        inputs['prompted'], 
        inputs['time_since_spoke'], 
        inputs['tod']
    ])
    y.append(entry['label'])

X = np.array(X)
y = np.array(y)

# 2. Scale the data
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# 3. Define and Train the Model
print("Training the 4-input brain on all rules...")
model = MLPClassifier(
    hidden_layer_sizes=(16, 16),
    max_iter=20_000,
    activation='relu',           
    solver='lbfgs',              
    alpha=0,                     
    random_state=42
)

model.fit(X_scaled, y)

# 4. Diagnostic
y_pred = model.predict(X_scaled)
accuracy = accuracy_score(y, y_pred)

print("-" * 30)
print(f"TRAINING COMPLETE")
print(f"Rule Adherence: {accuracy * 100:.2f}%")
print("-" * 30)

# 5. Detailed Report
print("Rule Consistency Report:")
target_names = ['Nothing', 'Hello', 'Goodbye', 'Fact']
report = classification_report(
    y, 
    y_pred, 
    labels=[0, 1, 2, 3], 
    target_names=target_names,
    zero_division=0 
)
print(report)

# 6. Safety Check: Verify 4-Input Logic
# Test 1: Awake, No Prompt, 10m silent, 2:00 PM (Fact/3)
# Test 2: Awake, No Prompt, 10m silent, 11:00 PM (Nothing/0 - Curfew)
# Test 3: Awake, PROMPTED, 10m silent, 11:00 PM (Fact/3 - Override)
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

# 7. Save the results
if accuracy > 0.9:
    config_loader.save_brain(model, scaler)
    print("\n[SUCCESS] 4-Input Brain saved.")
else:
    print("\n[WARNING] Accuracy too low. Brain not saved.")