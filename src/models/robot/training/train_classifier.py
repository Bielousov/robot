import json
import os
import sys
import time
import numpy as np
from pathlib import Path
from joblib import Parallel, delayed
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report

# --- INITIALIZATION ---
project_path = Path(__file__).parents[3].resolve()
if str(project_path) not in sys.path:
    sys.path.insert(0, str(project_path))

from config import Paths, ClassifierModelConfig
from lib.ModelManager import ModelManager

ACCURACY_TRESHOLD = 0.99
TRAINING_RESTARTS = os.cpu_count() or 1

manager = ModelManager(Paths)

try:
    training_data_path = Paths.ModelTrainingData
    if not Path(training_data_path).exists():
        raise FileNotFoundError(f"Training data file not found at: {training_data_path}")
    with open(training_data_path, 'r', encoding='utf-8') as f:
        raw_training_data = json.load(f)

except Exception as e:
    print(f"[Error] Could not load training data: {e}")
    sys.exit(1)

# --- DYNAMIC KEY DETECTION ---
# Every rule is a single exact (no ranges) input combination now - no
# Cartesian expansion needed, just read the values straight off.
input_keys = list(raw_training_data[0]['inputs'].keys())
X = np.array([[entry['inputs'][key] for key in input_keys] for entry in raw_training_data])
y = np.array([entry['label'] for entry in raw_training_data])

print(f"[System] Loaded {len(X)} training samples.")

# Start the overall timer
total_start_time = time.perf_counter()

# --- SCALING ---
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# --- TRAINING ---
print(
    f"[System] Training {TRAINING_RESTARTS} candidate networks in parallel ",
    end="", flush=True,
)

def _fit_candidate(seed):
    # A handful of random initializations occasionally diverge (exploding
    # ReLU/Adam activations) before settling or getting discarded below -
    # harmless since only the best candidate is kept, but numpy's matmul
    # floating-point warnings for that transient blowup are just noise at
    # this scale. Scoped around both fit and predict (and the caller reuses
    # this same prediction below instead of calling predict() again
    # unprotected) so real warnings elsewhere still surface normally.
    with np.errstate(all='ignore'):
        candidate = MLPClassifier(**ClassifierModelConfig, random_state=seed)
        candidate.fit(X_scaled, y)
        candidate_pred = candidate.predict(X_scaled)
    candidate_accuracy = accuracy_score(y, candidate_pred)
    return candidate, candidate_accuracy, candidate_pred

candidates = Parallel(n_jobs=TRAINING_RESTARTS)(
    delayed(_fit_candidate)(seed) for seed in range(TRAINING_RESTARTS)
)
print(" Done.")

# A diverged candidate's own recorded loss_ can come back NaN - max() with a
# NaN key is unreliable (NaN comparisons are always False), so it could
# otherwise end up "winning" the tie-break by accident depending on
# iteration order. Filter those out before picking the best of what's left.
finite_candidates = [c for c in candidates if np.isfinite(c[0].loss_)]
diverged = len(candidates) - len(finite_candidates)
if diverged:
    print(f"[System] {diverged}/{len(candidates)} candidate(s) diverged and were discarded.")
if not finite_candidates:
    print("[Error] All candidates diverged; no usable model to save.")
    sys.exit(1)

# Best candidate wins: highest training accuracy, ties broken by lowest loss.
# Reuses the prediction already computed (under errstate) in _fit_candidate
# rather than calling predict() again here unprotected.
model, accuracy, y_pred = max(finite_candidates, key=lambda c: (c[1], -c[0].loss_))

# --- DIAGNOSTICS ---
total_end_time = time.perf_counter()
total_duration = total_end_time - total_start_time

# --- FINAL SUMMARY ---
print("\n" + "="*40)
print(f"       BRAIN TRAINING RESULTS")
print("="*40)
print(f"Overall Process Time : {total_duration:.2f} seconds")
print(f"Unique Samples       : {len(X)}")
print(f"Feature Set          : {', '.join(input_keys)}")
print(f"Restarts Tried       : {TRAINING_RESTARTS} (best of, by accuracy/loss)")
print(f"Epochs Run           : {model.n_iter_} / {model.max_iter}")
print(f"Loss Score           : {model.loss_:.6f}")
print(f"Training Accuracy    : {accuracy * 100:.2f}%")
print("-" * 40)

# 6. Detailed Report
# Utterance ("free will" spontaneous speech) is deliberately not a class the
# Robot Model predicts at all - see State.get_context()'s docstring.
# IntentHandler decides it directly from State instead, so there's no gap to
# skip here: labels are the plain 0..4 range.
target_names = ['Nothing', 'Hello', 'Goodbye', 'Prompt', 'Speak']
print(classification_report(y, y_pred, labels=[0, 1, 2, 3, 4], target_names=target_names, zero_division=0))

# 8. Save
if accuracy > ACCURACY_TRESHOLD:
    manager.save(model, scaler)
    print(f"\n[SUCCESS] Brain saved to {Paths.Model}") 
else:
    print("\n[WARNING] Accuracy threshold not met. Save aborted.")