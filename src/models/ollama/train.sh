#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJECT_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../../.." && pwd)

PYTHON=${PYTHON:-$PROJECT_ROOT/.venv/bin/python}
BASE_MODEL=${BASE_MODEL:-Qwen/Qwen2.5-1.5B-Instruct}
ADAPTER_DIR=${ADAPTER_DIR:-$SCRIPT_DIR/build/adapters/pip-qwen2.5}
FUSED_DIR=${FUSED_DIR:-$SCRIPT_DIR/build/fused/pip-qwen2.5}
DATA_DIR=${DATA_DIR:-$SCRIPT_DIR/training/data}
TRAIN_ITERS=${TRAIN_ITERS:-300}
BATCH_SIZE=${BATCH_SIZE:-1}
LEARNING_RATE=${LEARNING_RATE:-1e-5}

require_file() {
    if [ ! -e "$1" ]; then
        echo "[train] ERROR: missing $1" >&2
        exit 1
    fi
}

require_command() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo "[train] ERROR: '$1' is not installed or not on PATH" >&2
        exit 1
    fi
}

require_file "$PYTHON"
require_file "$SCRIPT_DIR/training/personality.jsonl"
require_command "$PYTHON"

if ! "$PYTHON" -c "import torch; import peft; import transformers; import datasets" >/dev/null 2>&1; then
    echo "[train] ERROR: PyTorch/PEFT/Transformers/Datasets missing from $PYTHON" >&2
    echo "[train] Install with: $PYTHON -m pip install torch peft transformers datasets" >&2
    exit 1
fi

printf '%s\n' "[train] Preparing dataset"

# Download base model once (cached for subsequent runs)
printf '%s\n' "[train] Ensuring base model is cached..."
"$PYTHON" - "$BASE_MODEL" <<'DOWNLOAD_MODEL'
import sys
from huggingface_hub import snapshot_download

model_name = sys.argv[1]
print(f"[train] Checking cache for {model_name}...")
cache_dir = snapshot_download(model_name, cache_dir=None, resume_download=True)
print(f"[train] Model cached at: {cache_dir}")
DOWNLOAD_MODEL

# Create build/data
mkdir -p "$DATA_DIR"

# Split personality.jsonl into train/validation sets.
# Uses deterministic pseudo-random ordering with seed 7.
"$PYTHON" "$SCRIPT_DIR/training/prepare_data.py" \
    "$SCRIPT_DIR/training/personality.jsonl" \
    "$DATA_DIR"

require_file "$DATA_DIR/train.jsonl"
require_file "$DATA_DIR/valid.jsonl"

printf '%s\n' "[train] Training LoRA adapter with PyTorch"
mkdir -p "$ADAPTER_DIR"

"$PYTHON" "$SCRIPT_DIR/training/train_adapter.py" \
    "$BASE_MODEL" \
    "$DATA_DIR" \
    "$ADAPTER_DIR" \
    "$TRAIN_ITERS" \
    "$BATCH_SIZE" \
    "$LEARNING_RATE"

require_file "$ADAPTER_DIR/adapter_config.json"

printf '%s\n' "[train] Merging adapter with base model"
rm -rf "$FUSED_DIR"
mkdir -p "$FUSED_DIR"

"$PYTHON" "$SCRIPT_DIR/training/merge_adapter.py" \
    "$BASE_MODEL" \
    "$ADAPTER_DIR" \
    "$FUSED_DIR"

require_file "$FUSED_DIR/config.json"

printf '%s\n' "[train] ============================================"
printf '%s\n' "[train] Training complete!"
printf '%s\n' "[train] ============================================"
printf '%s\n' "[train]"
printf '%s\n' "[train] Adapter:        $ADAPTER_DIR"
printf '%s\n' "[train] Merged model:   $FUSED_DIR"
printf '%s\n' "[train]"
printf '%s\n' "[train] The merged model is ready for Hailo HEF conversion."
printf '%s\n' "[train] Next steps:"
printf '%s\n' "[train]   1. Convert to Hailo HEF using Hailo's compiler"
printf '%s\n' "[train]   2. Or use the HF model directly with Ollama on CPU"
printf '%s\n' "[train] ============================================"