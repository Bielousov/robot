import numpy as np
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
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

# 2. Split data: 80% for training, 20% for testing
# random_state ensures you get the same results every time you run it
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# 3. Scale the data
scaler = StandardScaler()
# Important: Fit the scaler ONLY on the training data
X_train_scaled = scaler.fit_transform(X_train)
# Just transform the test data (don't let the scaler "see" the answers)
X_test_scaled = scaler.transform(X_test)

# 4. Define and Train the Model
print("Training the brain...")
model = MLPClassifier(
    hidden_layer_sizes=(6, 4),      # Fewer neurons = better for tiny data
    max_iter=10_000,                  # Give it more time to converge
    activation='relu',              # Industry standard for hidden layers
    solver='adam',                  # Robust optimizer
    learning_rate_init=0.01,        # Faster learning
    random_state=42                 # Keeps results consistent
)
model.fit(X_train_scaled, y_train)

# 5. Calculate Accuracy
y_pred = model.predict(X_test_scaled)
accuracy = accuracy_score(y_test, y_pred)

print("-" * 30)
print(f"TRAINING COMPLETE")
print(f"Model Accuracy: {accuracy * 100:.2f}%")
print("-" * 30)

# Optional: Print a detailed report if you have enough data
if len(X) > 0:
    print("Detailed Performance Report:")
    target_names = ['Nothing', 'Hello', 'Goodbye', 'Fact']
    
    # Adding zero_division=0 removes the messy traceback warnings
    report = classification_report(
        y_test, 
        y_pred, 
        labels=[0, 1, 2, 3], 
        target_names=target_names,
        zero_division=0 
    )
    print(report)

# 6. Save the results
config_loader.save_brain(model, scaler)