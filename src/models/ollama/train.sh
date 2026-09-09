#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJECT_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../../.." && pwd)
PYTHON=${PYTHON:-$PROJECT_ROOT/.venv/bin/python}

# Load .env if it exists
if [ -f "$PROJECT_ROOT/.env" ]; then
    set -a
    . "$PROJECT_ROOT/.env"
    set +a
fi

BASE_MODEL=${BASE_MODEL:-${OLLAMA_BASE_MODEL:-Qwen/Qwen2.5-1.5B-Instruct}}
MODEL_NAME=${OLLAMA_MODEL_NAME:-pip}

ADAPTER_DIR=${ADAPTER_DIR:-$SCRIPT_DIR/build/adapters/$MODEL_NAME}
FUSED_DIR=${FUSED_DIR:-$SCRIPT_DIR/build/fused/$MODEL_NAME}
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

printf '%s\n' "[train] Training LoRA adapter with PyTorch (aarch64)"
mkdir -p "$ADAPTER_DIR"

"$PYTHON" "$SCRIPT_DIR/training/aarch64/train_adapter.py" \
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

"$PYTHON" "$SCRIPT_DIR/training/aarch64/merge_adapter.py" \
    "$BASE_MODEL" \
    "$ADAPTER_DIR" \
    "$FUSED_DIR"

require_file "$FUSED_DIR/config.json"

printf '%s\n' "[train] Creating Ollama model (HF format, CPU-based)..."
MODELFILE="$SCRIPT_DIR/training/Modelfile.$MODEL_NAME"

cat > "$MODELFILE" <<EOF
FROM $FUSED_DIR

TEMPLATE """{{- if .Messages }}
{{- range .Messages }}
{{- if eq .Role "system" }}<|im_start|>system
{{ .Content }}<|im_end|>
{{- else if eq .Role "user" }}<|im_start|>user
{{ .Content }}<|im_end|>
{{- else if eq .Role "assistant" }}<|im_start|>assistant
{{ .Content }}<|im_end|>
{{- end }}
{{- end }}
{{- end }}<|im_start|>assistant
"""

PARAMETER stop "<|im_end|>"
SYSTEM "You are Pip, an autonomous robot. Reply briefly and directly. Do not describe yourself as an AI assistant."
EOF

if command -v ollama >/dev/null 2>&1; then
    ollama create "$MODEL_NAME" -f "$MODELFILE"
    printf '%s\n' "[train] Created Ollama model: $MODEL_NAME"
else
    printf '%s\n' "[train] Ollama not found - skipping model creation"
    printf '%s\n' "[train] To create manually: ollama create $MODEL_NAME -f $MODELFILE"
fi

printf '%s\n' "[train] ============================================"
printf '%s\n' "[train] Training complete!"
printf '%s\n' "[train] ============================================"
printf '%s\n' "[train]"
printf '%s\n' "[train] Model name:     $MODEL_NAME"
printf '%s\n' "[train] Merged model:   $FUSED_DIR"
printf '%s\n' "[train]"
printf '%s\n' "[train] Usage:"
printf '%s\n' "[train]   ollama run $MODEL_NAME \"Your prompt here\""
printf '%s\n' "[train]"
printf '%s\n' "[train] For Hailo HEF conversion:"
printf '%s\n' "[train]   1. Use $FUSED_DIR (HF format)"
printf '%s\n' "[train]   2. Convert with Hailo's compiler"
printf '%s\n' "[train] ============================================"