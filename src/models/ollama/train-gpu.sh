#!/bin/sh
set -eu

# GPU training script for Mac M1+ using MLX (Apple's ML framework)
# Much faster than CPU training: ~100x speedup on M1

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

if ! "$PYTHON" -c "import mlx_lm" >/dev/null 2>&1; then
    echo "[train] ERROR: MLX is not installed" >&2
    echo "[train] Install with: $PYTHON -m pip install mlx mlx-lm" >&2
    exit 1
fi

if ! command -v ollama >/dev/null 2>&1; then
    echo "[train] Warning: ollama not found - model creation will be skipped"
fi

printf '%s\n' "[train] ========== GPU Training (MLX) =========="
printf '%s\n' "[train] Base model: $BASE_MODEL"
printf '%s\n' "[train] Training on Mac M1+ GPU with MLX"
printf '%s\n' "[train]"

printf '%s\n' "[train] Preparing dataset"
mkdir -p "$DATA_DIR"

"$PYTHON" "$SCRIPT_DIR/training/prepare_data.py" \
    "$SCRIPT_DIR/training/personality.jsonl" \
    "$DATA_DIR"

require_file "$DATA_DIR/train.jsonl"
require_file "$DATA_DIR/valid.jsonl"

printf '%s\n' "[train] Training LoRA adapter (MLX GPU)"
mkdir -p "$ADAPTER_DIR"

"$PYTHON" "$SCRIPT_DIR/training/train_adapter_gpu.py" \
    "$BASE_MODEL" \
    "$DATA_DIR" \
    "$ADAPTER_DIR" \
    "$TRAIN_ITERS" \
    "$BATCH_SIZE" \
    "$LEARNING_RATE"

require_file "$ADAPTER_DIR/adapters.safetensors"

printf '%s\n' "[train] Merging adapter with base model"
rm -rf "$FUSED_DIR"
mkdir -p "$FUSED_DIR"

"$PYTHON" "$SCRIPT_DIR/training/merge_adapter_gpu.py" \
    "$BASE_MODEL" \
    "$ADAPTER_DIR" \
    "$FUSED_DIR"

require_file "$FUSED_DIR/config.json"

printf '%s\n' "[train] Creating Ollama model (HF format, CPU-based)"
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
printf '%s\n' "[train] Training complete (GPU)!"
printf '%s\n' "[train] ============================================"
printf '%s\n' "[train]"
printf '%s\n' "[train] Model name:     $MODEL_NAME"
printf '%s\n' "[train] Merged model:   $FUSED_DIR"
printf '%s\n' "[train]"
printf '%s\n' "[train] To upload to RPi5:"
printf '%s\n' "[train]   rsync -av $FUSED_DIR pip@robot:/home/pip/robot/src/models/ollama/build/fused/$MODEL_NAME"
printf '%s\n' "[train]"
printf '%s\n' "[train] Usage:"
printf '%s\n' "[train]   ollama run $MODEL_NAME \"Your prompt here\""
printf '%s\n' "[train] ============================================"
