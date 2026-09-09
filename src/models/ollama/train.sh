#!/bin/sh
set -eu

# Universal LoRA training script - auto-detects platform and training backend
# - Mac M1+ with MLX: GPU training (fast)
# - RPi5/Linux/Mac CPU: PyTorch CPU training (universal)

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
HF_TOKEN=${HF_TOKEN:-}

ADAPTER_DIR=${ADAPTER_DIR:-$SCRIPT_DIR/build/adapters/$MODEL_NAME}
FUSED_DIR=${FUSED_DIR:-$SCRIPT_DIR/build/fused/$MODEL_NAME}
DATA_DIR=${DATA_DIR:-$SCRIPT_DIR/training/build}
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

# Detect platform and training backend
detect_backend() {
    SYSTEM=$(uname -s)

    # Try to use GPU training on macOS if MLX is available
    if [ "$SYSTEM" = "Darwin" ]; then
        if "$PYTHON" -c "import mlx_lm" >/dev/null 2>&1; then
            echo "darwin"
            return 0
        fi
    fi

    # Default to CPU training (works everywhere)
    echo "aarch64"
}

BACKEND=$(detect_backend)

printf '%s\n' "[train] =========================================="
printf '%s\n' "[train] LoRA Personality Training"
printf '%s\n' "[train] =========================================="
printf '%s\n' "[train] Backend: $BACKEND"
printf '%s\n' "[train] Base model: $BASE_MODEL"
printf '%s\n' "[train]"

case "$BACKEND" in
    darwin)
        printf '%s\n' "[train] Using MLX GPU training (Mac M1+)"
        ;;
    aarch64)
        printf '%s\n' "[train] Using PyTorch CPU training (universal)"
        ;;
esac

printf '%s\n' "[train]"

require_file "$PYTHON"
require_file "$SCRIPT_DIR/training/personality.jsonl"
require_command "$PYTHON"

# Verify dependencies
case "$BACKEND" in
    darwin)
        if ! "$PYTHON" -c "import mlx_lm" >/dev/null 2>&1; then
            echo "[train] ERROR: MLX is not installed" >&2
            echo "[train] Install with: $PYTHON -m pip install mlx mlx-lm" >&2
            exit 1
        fi
        ;;
    aarch64)
        if ! "$PYTHON" -c "import torch; import peft; import transformers; import datasets" >/dev/null 2>&1; then
            echo "[train] ERROR: PyTorch/PEFT/Transformers/Datasets missing" >&2
            echo "[train] Install with: $PYTHON -m pip install torch peft transformers datasets" >&2
            exit 1
        fi
        ;;
esac

if ! command -v ollama >/dev/null 2>&1; then
    echo "[train] Warning: ollama not found - model creation will be skipped"
fi

printf '%s\n' "[train] Preparing dataset"
mkdir -p "$DATA_DIR"

"$PYTHON" "$SCRIPT_DIR/training/prepare_data.py" \
    "$SCRIPT_DIR/training/personality.jsonl" \
    "$DATA_DIR"

require_file "$DATA_DIR/train.jsonl"
require_file "$DATA_DIR/valid.jsonl"

printf '%s\n' "[train] Training LoRA adapter"
mkdir -p "$ADAPTER_DIR"

HF_TOKEN="$HF_TOKEN" "$PYTHON" "$SCRIPT_DIR/training/$BACKEND/train_adapter.py" \
    "$BASE_MODEL" \
    "$DATA_DIR" \
    "$ADAPTER_DIR" \
    "$TRAIN_ITERS" \
    "$BATCH_SIZE" \
    "$LEARNING_RATE"

# MLX and PyTorch produce different files, so just check directory is not empty
if [ ! -d "$ADAPTER_DIR" ] || [ -z "$(ls -A $ADAPTER_DIR 2>/dev/null)" ]; then
    echo "[train] ERROR: Adapter directory is empty: $ADAPTER_DIR" >&2
    exit 1
fi

printf '%s\n' "[train] Merging adapter with base model"
rm -rf "$FUSED_DIR"
mkdir -p "$FUSED_DIR"

HF_TOKEN="$HF_TOKEN" "$PYTHON" "$SCRIPT_DIR/training/$BACKEND/merge_adapter.py" \
    "$BASE_MODEL" \
    "$ADAPTER_DIR" \
    "$FUSED_DIR"

require_file "$FUSED_DIR/config.json"

printf '%s\n' "[train] Creating Ollama model"
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
printf '%s\n' "[train] Backend:        $BACKEND"
printf '%s\n' "[train]"
printf '%s\n' "[train] To upload to RPi5:"
printf '%s\n' "[train]   rsync -av $FUSED_DIR pip:/home/pip/robot/src/models/ollama/build/fused/$MODEL_NAME"
printf '%s\n' "[train]"
printf '%s\n' "[train] Usage:"
printf '%s\n' "[train]   ollama run $MODEL_NAME \"Your prompt here\""
printf '%s\n' "[train] ============================================"
