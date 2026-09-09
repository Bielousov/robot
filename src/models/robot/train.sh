#!/bin/bash
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJECT_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../../.." && pwd)

PYTHON=${PYTHON:-$PROJECT_ROOT/.venv/bin/python}

if [ ! -f "$PYTHON" ]; then
    echo "[train] ERROR: Python not found at $PYTHON" >&2
    exit 1
fi

"$PYTHON" "$SCRIPT_DIR/training/train.py"
