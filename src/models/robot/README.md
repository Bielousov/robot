# Robot Brain Model

The Robot Model is a scikit-learn `MLPClassifier` (16×16 hidden layers) + `StandardScaler` that turns a 5-value numeric snapshot of the robot's state into an **intent** (idle/sleep/wake/prompt/speak).

Spontaneous "utterance" (free will) is deliberately **not** one of the model's
classes - it was a narrow, rare region that a generic classifier couldn't
reliably separate from the broad "nothing to do" rules surrounding it once
its random `chaos` gating feature was removed. It's decided directly in code
instead: `IntentHandler.handle()` (`src/intents.py`) calls
`Utterances.consider()` (`src/utterances.py`) from its own `action == 0`
branch, which hard-gates on `State.eavesdropped_context`/`State.time_since_heard`
(below either floor, not eligible at all) and, once past both, looks up a
confidence from a **second, separate model** - a small `MLPRegressor`
(`utterance_model.pkg`) fit over both values, since a continuous surface is
exactly what neural nets are good at (unlike the sharp classification
boundary the first attempt needed). More overheard context raises confidence
even at the same time_since_heard, not just longer silence. That confidence
then feeds a coin flip (`confidence * random() > random()`) rather than
firing automatically.

## Training

Two independent models live here, each with its own training data and script:

| Model                                   | Purpose                                            | Training data                                 | Script                         |
| --------------------------------------- | -------------------------------------------------- | --------------------------------------------- | ------------------------------ |
| Robot Model (`classifier_model.pkg`)    | idle/sleep/wake/prompt/speak classification        | `training/data/classifier_training_data.json` | `training/classifier_train.py` |
| Utterance Model (`utterance_model.pkg`) | `(eavesdropped_context, time_since_heard)` -> "free will" confidence | `training/data/utterance_training_data.json`  | `training/train_utterance.py`  |

The classifier's training data is a direct list of labeled examples - each rule is one exact input combination, read straight into the training set (no ranges, no expansion). The regressor's training data is likewise a direct list, but of `(eavesdropped_context, time_since_heard, confidence)` points describing the target surface - there's no classification step, just curve-fitting.

### Quick Start

```bash
# From the project root, run both:
./src/models/robot/train.sh
```

Or directly:

```bash
python src/models/robot/training/classifier_train.py  # Robot Model
python src/models/robot/training/train_utterance.py   # Utterance Model
```

### Requirements

- Python ≥ 3.11 (for numpy ≥ 2.3.4 and scikit-learn ≥ 1.9.0)
- Dependencies from `requirements.txt`: `numpy==2.3.4`, `scikit-learn==1.9.0`, `joblib`, `python-dotenv`
- `.env` file with config (optional; defaults exist)

### Environment

Ensure `requirements.txt` versions match your venv:

```bash
.venv/bin/pip install -r requirements.txt
```

Pickle compatibility (`*.pkg` files) depends on numpy/scikit-learn versions. If you get `MT19937 is not a known BitGenerator`, reinstall the pinned versions above and retrain.

### Output

On success, `classifier_train.py` writes:

- `classifier_model.pkg` — pickled `MLPClassifier`
- `classifier_scaler.pkg` — pickled `StandardScaler`

Accuracy must exceed the threshold (0.99 by default, set in `classifier_train.py` as `ACCURACY_TRESHOLD`). If not met, the .pkg files are not saved and you'll see a warning.

`train_utterance.py` writes `utterance_model.pkg`/`utterance_scaler.pkg` the same way, gated on `R2_THRESHOLD`/`MSE_THRESHOLD` instead of accuracy (it's a regression fit, not a classification).

### Configuration

Edit `training/data/classifier_training_data.json` to add or modify the classifier's decision rules. Each rule has:

- `"description"` — human label (unused at runtime, for debugging)
- `"inputs"` — dict of exact feature values (no ranges)
- `"label"` — intent (0=idle, 1=sleep, 2=wake, 3=prompt, 4=speak)

Features are fixed and must match what `State.get_context()` returns:

```
awake_phase, has_pending_prompt, is_thinking, has_pending_response,
is_speaking
```

Edit `training/data/utterance_training_data.json` to reshape the free-will confidence surface instead. Each entry is a single `(eavesdropped_context, time_since_heard, confidence)` point:

```json
{ "inputs": { "eavesdropped_context": 40, "time_since_heard": 20 }, "confidence": 0.4750 }
```

Add, remove, or re-value points to change the surface's shape - there's no
"correct" surface, just whatever behavior feels right. Keep it continuous
(no sudden jumps between adjacent points in either dimension) -
`MLPRegressor` can trace a sharp corner fairly well, but not a true
discontinuity, so training will undershoot the fit and may not clear the
accuracy thresholds.

### Debugging

Add `DEBUG=1` to `.env` or pass it to the Python interpreter to see per-iteration logs.
