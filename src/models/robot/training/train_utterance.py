import json
import os
import sys
import time
import numpy as np
from pathlib import Path
from joblib import Parallel, delayed
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score

# --- INITIALIZATION ---
project_path = Path(__file__).parents[3].resolve()
if str(project_path) not in sys.path:
    sys.path.insert(0, str(project_path))

from config import Paths, UtteranceModelConfig
from lib.ModelManager import ModelManager

# Regression, not classification: there's no discrete "right answer" to be
# accurate about, just a curve to fit. R^2 close to 1 means the model
# reproduces the training curve closely; MSE is the same thing in absolute
# terms (confidence is scaled 0..1, so 0.01 MSE is a small, believable
# fitting error - the curve has two corners a small ReLU net can't trace
# perfectly, just very closely).
R2_THRESHOLD = 0.95
MSE_THRESHOLD = 0.01
TRAINING_RESTARTS = os.cpu_count() or 1

manager = ModelManager(Paths)

try:
    training_data_path = Paths.UtteranceTrainingData
    if not Path(training_data_path).exists():
        raise FileNotFoundError(f"Training data file not found at: {training_data_path}")
    with open(training_data_path, 'r', encoding='utf-8') as f:
        raw_training_data = json.load(f)

except Exception as e:
    print(f"[Error] Could not load training data: {e}")
    sys.exit(1)

# --- DYNAMIC KEY DETECTION ---
input_keys = list(raw_training_data[0]['inputs'].keys())
X = np.array([[entry['inputs'][key] for key in input_keys] for entry in raw_training_data])
y = np.array([entry['confidence'] for entry in raw_training_data], dtype=float)

print(f"[System] Loaded {len(X)} training points.")

# Start the overall timer
total_start_time = time.perf_counter()

# --- SCALING ---
# Only X is scaled - y (confidence) is already a bounded 0..1 target, and
# MLPRegressor's predictions are clipped to that range at inference time
# anyway (see Utterances._predict_confidence in src/utterances.py).
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
        candidate = MLPRegressor(**UtteranceModelConfig, random_state=seed)
        candidate.fit(X_scaled, y)
        candidate_pred = candidate.predict(X_scaled)
    candidate_mse = mean_squared_error(y, candidate_pred)
    return candidate, candidate_mse, candidate_pred

candidates = Parallel(n_jobs=TRAINING_RESTARTS)(
    delayed(_fit_candidate)(seed) for seed in range(TRAINING_RESTARTS)
)
print(" Done.")

# A diverged candidate's MSE can come back NaN - min() with a NaN key is
# unreliable (NaN comparisons are always False), so it could otherwise end
# up "winning" by accident depending on iteration order. Filter those out
# before picking the best of what's left.
finite_candidates = [c for c in candidates if np.isfinite(c[1])]
diverged = len(candidates) - len(finite_candidates)
if diverged:
    print(f"[System] {diverged}/{len(candidates)} candidate(s) diverged and were discarded.")
if not finite_candidates:
    print("[Error] All candidates diverged; no usable model to save.")
    sys.exit(1)

# Best candidate wins: lowest training MSE. Reuses the prediction already
# computed (under errstate) in _fit_candidate rather than calling predict()
# again here unprotected.
model, mse, y_pred = min(finite_candidates, key=lambda c: c[1])

# --- DIAGNOSTICS ---
r2 = r2_score(y, y_pred)
total_end_time = time.perf_counter()
total_duration = total_end_time - total_start_time

# --- FINAL SUMMARY ---
print("\n" + "="*40)
print(f"    UTTERANCE CONFIDENCE TRAINING RESULTS")
print("="*40)
print(f"Overall Process Time : {total_duration:.2f} seconds")
print(f"Training Points      : {len(X)}")
print(f"Feature Set          : {', '.join(input_keys)}")
print(f"Restarts Tried       : {TRAINING_RESTARTS} (best of, by MSE)")
print(f"Epochs Run           : {model.n_iter_} / {model.max_iter}")
print(f"Loss Score           : {model.loss_:.6f}")
print(f"Training MSE         : {mse:.6f}")
print(f"Training R^2         : {r2:.4f}")
print("-" * 40)

# 8. Save
if mse < MSE_THRESHOLD and r2 > R2_THRESHOLD:
    manager.save(model, scaler, model_key="UtteranceModel", scaler_key="UtteranceModelScaler")
    print(f"\n[SUCCESS] Utterance model saved to {Paths.UtteranceModel}")
else:
    print("\n[WARNING] Fit quality threshold not met. Save aborted.")
