# Robot Brain Model

The Robot Model is a scikit-learn `MLPClassifier` (16×16 hidden layers) + `StandardScaler` that turns an 8-value numeric snapshot of the robot's state into an **intent** (idle/sleep/wake/prompt/utter/speak).

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

Accuracy must exceed the threshold (0.95 by default, set in `train.py` as `ACCURACY_TRESHOLD`). If not met, the .pkg files are not saved and you'll see a warning.

### Configuration

Edit `data/training_data.json` to add or modify decision rules. Each rule has:
- `"description"` — human label (unused at runtime, for debugging)
- `"inputs"` — dict of feature ranges/values
- `"label"` — intent (0=idle, 1=sleep, 2=wake, 3=prompt, 4=utterance, 5=speak)

Features are fixed and must match what `State.get_context()` returns:
```
chaos, awake_phase, has_pending_prompt, is_thinking,
has_pending_response, is_speaking, time_since_spoke, tod
```

### Debugging

Add `DEBUG=1` to `.env` or pass it to the Python interpreter to see per-iteration logs.
