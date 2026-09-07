#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJECT_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../../../.." && pwd)

PYTHON=${PYTHON:-$PROJECT_ROOT/.venv-mlx/bin/python}
BASE_MODEL=${BASE_MODEL:-$HOME/.cache/mlx-models/Qwen2.5-1.5B-Instruct-4bit}
LLAMA_CPP_DIR=${LLAMA_CPP_DIR:-$HOME/src/llama.cpp}
ADAPTER_DIR=${ADAPTER_DIR:-$SCRIPT_DIR/build/adapters/pip-qwen2.5}
FUSED_DIR=${FUSED_DIR:-$SCRIPT_DIR/build/fused/pip-qwen2.5}
F16_GGUF=${F16_GGUF:-$SCRIPT_DIR/build/pip-qwen2.5-f16.gguf}
Q4_GGUF=${Q4_GGUF:-$SCRIPT_DIR/build/pip-qwen2.5-q4_k_m.gguf}
OLLAMA_MODEL=${OLLAMA_MODEL:-pip-personality}
DATA_DIR=${DATA_DIR:-$SCRIPT_DIR/build/data}
TRAIN_ITERS=${TRAIN_ITERS:-300}
BATCH_SIZE=${BATCH_SIZE:-1}
NUM_LAYERS=${NUM_LAYERS:-8}
LEARNING_RATE=${LEARNING_RATE:-1e-5}
SKIP_OLLAMA=${SKIP_OLLAMA:-0}

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
require_file "$BASE_MODEL"
require_file "$SCRIPT_DIR/personality.jsonl"
require_file "$LLAMA_CPP_DIR/convert_hf_to_gguf.py"
require_file "$LLAMA_CPP_DIR/build/bin/llama-quantize"
require_command "$PYTHON"

if ! "$PYTHON" -c "import mlx_lm" >/dev/null 2>&1; then
    echo "[train] ERROR: mlx-lm is missing from $PYTHON" >&2
    echo "[train] Install it with: $PYTHON -m pip install mlx mlx-lm" >&2
    exit 1
fi

if [ "$SKIP_OLLAMA" != "1" ]; then
    require_command ollama
fi

printf '%s\n' "[train] Preparing dataset"

# Create build/data
mkdir -p "$DATA_DIR"

# Split personality.jsonl into train/validation sets.
# Uses awk for deterministic pseudo-random ordering with seed 7.
"$PYTHON" - "$SCRIPT_DIR/personality.jsonl" "$DATA_DIR" <<'PY'
import json
import random
import sys
from pathlib import Path

source = Path(sys.argv[1])
output = Path(sys.argv[2])

rows = [
    json.loads(line)
    for line in source.read_text().splitlines()
    if line.strip()
]

random.Random(7).shuffle(rows)

validation_count = max(4, round(len(rows) * 0.15))

output.mkdir(parents=True, exist_ok=True)

(output / "valid.jsonl").write_text(
    "".join(json.dumps(row) + "\n" for row in rows[:validation_count])
)

(output / "train.jsonl").write_text(
    "".join(json.dumps(row) + "\n" for row in rows[validation_count:])
)

print(f"[train] train={len(rows) - validation_count}, valid={validation_count}")
PY

require_file "$DATA_DIR/train.jsonl"
require_file "$DATA_DIR/valid.jsonl"

printf '%s\n' "[train] Training LoRA adapter"
"$PYTHON" -m mlx_lm lora \
    --model "$BASE_MODEL" \
    --data "$DATA_DIR" \
    --train \
    --iters "$TRAIN_ITERS" \
    --batch-size "$BATCH_SIZE" \
    --num-layers "$NUM_LAYERS" \
    --learning-rate "$LEARNING_RATE" \
    --adapter-path "$ADAPTER_DIR"

require_file "$ADAPTER_DIR/build/adapters.safetensors"

printf '%s\n' "[train] Fusing adapter into dequantized model"
rm -rf "$FUSED_DIR"
"$PYTHON" -m mlx_lm fuse \
    --model "$BASE_MODEL" \
    --adapter-path "$ADAPTER_DIR" \
    --save-path "$FUSED_DIR" \
    --dequantize

require_file "$FUSED_DIR/config.json"

printf '%s\n' "[train] Converting fused model to F16 GGUF"
"$PYTHON" "$LLAMA_CPP_DIR/convert_hf_to_gguf.py" \
    "$FUSED_DIR" \
    --outfile "$F16_GGUF" \
    --outtype f16

require_file "$F16_GGUF"

printf '%s\n' "[train] Quantizing GGUF to Q4_K_M"
"$LLAMA_CPP_DIR/build/bin/llama-quantize" \
    "$F16_GGUF" \
    "$Q4_GGUF" \
    Q4_K_M

require_file "$Q4_GGUF"

if [ "$SKIP_OLLAMA" = "1" ]; then
    printf '%s\n' "[train] Finished. Ollama creation skipped (SKIP_OLLAMA=1)."
    printf 'Q4 model: %s\n' "$Q4_GGUF"
    exit 0
fi

printf '%s\n' "[train] Creating Ollama model"
OLLAMAFILE="$PROJECT_ROOT/Modelfile.pip"

cat > "$OLLAMAFILE" <<EOF
FROM $Q4_GGUF

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
SYSTEM "You are Pip, an autonomous robot. Reply briefly and directly. Do not describe yourself as Qwen or as an AI assistant."
EOF

ollama create "$OLLAMA_MODEL" -f "$OLLAMAFILE"
printf '%s\n' "[train] Complete: $OLLAMA_MODEL"