#!/bin/bash
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJECT_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../../.." && pwd)

PYTHON=${PYTHON:-$PROJECT_ROOT/.venv/bin/python}

"$PYTHON" "$SCRIPT_DIR/training/train_classifier.py"
"$PYTHON" "$SCRIPT_DIR/training/train_utterance.py"
