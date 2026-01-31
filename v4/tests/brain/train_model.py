import numpy as np
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report
import config_loader 

# 1. Load Data
try:
    raw_data = config_loader.load_json("training_data")
except FileNotFoundError as e:
    print(e)
    exit()

X = []
y = []
for entry in raw_data:
    inputs = entry['inputs']
    X.append([inputs['awake'], inputs['time_since_spoke'], inputs['tod']])
    y.append(entry['label'])

X = np.array(X)
y = np.array(y)

# 2. Scale the data (Full Set)
# With tiny data, we want the scaler to see everything to establish true bounds
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# 3. Define and Train the Model
print("Training the brain on all rules...")
model = MLPClassifier(
    hidden_layer_sizes=(16, 16), # Capacity to 'memorize' the specific curfew hours
    max_iter=20_000,
    activation='relu',           
    solver='lbfgs',              # Optimal for datasets < 200 samples
    alpha=0,                     # Zero regularization forces strict rule adherence
    random_state=42
)

# We fit on the ENTIRE dataset
model.fit(X_scaled, y)

# 4. Diagnostic: Check if the brain learned the rules perfectly
y_pred = model.predict(X_scaled)
accuracy = accuracy_score(y, y_pred)

print("-" * 30)
print(f"TRAINING COMPLETE")
print(f"Rule Adherence: {accuracy * 100:.2f}%")
print("-" * 30)

# 5. Detailed Report on Rule Adherence
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

# 6. Safety Check: Verify Curfew logic manually
# Test: Awake, 10 mins silent, 2:00 PM (Should be Fact/3)
# Test: Awake, 10 mins silent, 11:00 PM (Should be Nothing/0)
test_points = np.array([
    [1, 10.0, 14.0], 
    [1, 10.0, 23.0]
])
test_scaled = scaler.transform(test_points)
test_preds = model.predict(test_scaled)

print("Curfew Verification:")
print(f" - 2:00 PM + 10m silence: {'PASS' if test_preds[0] == 3 else 'FAIL'} (Predicted {target_names[test_preds[0]]})")
print(f" - 11:00 PM + 10m silence: {'PASS' if test_preds[1] == 0 else 'FAIL'} (Predicted {target_names[test_preds[1]]})")

# 7. Save the results
if accuracy > 0.9:
    config_loader.save_brain(model, scaler)
    print("\n[SUCCESS] Brain saved with high rule adherence.")
else:
    print("\n[WARNING] Brain not saved. Accuracy too low to ensure reliable behavior.")