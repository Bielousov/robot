# Robot Brain Model

The Robot Model is a scikit-learn `MLPClassifier` (16×16 hidden layers) + `StandardScaler` that turns a 5-value numeric snapshot of the robot's state into an **intent** (idle/sleep/wake/prompt/speak).

Spontaneous "utterance" (free will) is deliberately **not** one of the model's
classes - it was a narrow, rare region that a generic classifier couldn't
reliably separate from the broad "nothing to do" rules surrounding it once
its random `chaos` gating feature was removed. It's decided directly in code
instead: `IntentHandler.handle()` (`src/intents.py`) calls
`Utterances.consider()` (`src/utterances.py`) from its own `action == 0`
branch, which checks `State.eavesdropped_context`/`State.time_since_heard`
and applies a confidence-weighted coin flip (`confidence * random() > random()`)
rather than firing automatically.

## Training

The model is trained on `data/training_data.json`, which defines decision rules as labeled examples. Each rule has numeric ranges for inputs; training expands those ranges into a Cartesian product of discrete samples and deduplicates them.

### Quick Start

```bash
# From the project root, run:
./src/models/robot/train.sh
```

Or directly:

```bash
python src/models/robot/train.py
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

Pickle compatibility (model.pkg/scaler.pkg) depends on numpy/scikit-learn versions. If you get `MT19937 is not a known BitGenerator`, reinstall the pinned versions above and retrain.

### Output

On success, writes:

- `model.pkg` — pickled `MLPClassifier`
- `scaler.pkg` — pickled `StandardScaler`

Accuracy must exceed the threshold (0.99 by default, set in `train.py` as `ACCURACY_TRESHOLD`). If not met, the .pkg files are not saved and you'll see a warning.

### Configuration

Edit `data/training_data.json` to add or modify decision rules. Each rule has:

- `"description"` — human label (unused at runtime, for debugging)
- `"inputs"` — dict of feature ranges/values
- `"label"` — intent (0=idle, 1=sleep, 2=wake, 3=prompt, 5=speak; 4=utterance
  is intentionally never used here - see above)

Features are fixed and must match what `State.get_context()` returns:

```
awake_phase, has_pending_prompt, is_thinking, has_pending_response,
is_speaking
```

### Debugging

Add `DEBUG=1` to `.env` or pass it to the Python interpreter to see per-iteration logs.
