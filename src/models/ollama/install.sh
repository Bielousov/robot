#!/bin/sh
set -eu

# Creates the Ollama model from an already-trained/uploaded model folder
# (build/$MODEL_NAME/, produced by train.sh and rsynced over as a whole).
# Run this on the target machine (e.g. the RPi5) after uploading.

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJECT_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../../.." && pwd)

# Load .env if it exists
if [ -f "$PROJECT_ROOT/.env" ]; then
    set -a
    . "$PROJECT_ROOT/.env"
    set +a
fi

MODEL_NAME=${1:-${OLLAMA_MODEL_NAME:-pip}}

BUILD_DIR=${BUILD_DIR:-$SCRIPT_DIR/build/$MODEL_NAME}
MODELFILE="$BUILD_DIR/Modelfile"
FUSED_DIR="$BUILD_DIR/fused"

require_file() {
    if [ ! -e "$1" ]; then
        echo "[install] ERROR: missing $1" >&2
        exit 1
    fi
}

require_command() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo "[install] ERROR: '$1' is not installed or not on PATH" >&2
        exit 1
    fi
}

require_command ollama

printf '%s\n' "[install] Model name: $MODEL_NAME"
printf '%s\n' "[install] Model folder: $BUILD_DIR"

require_file "$MODELFILE"
require_file "$FUSED_DIR"

if [ -z "$(ls -A "$FUSED_DIR" 2>/dev/null)" ]; then
    echo "[install] ERROR: Fused model directory is empty: $FUSED_DIR" >&2
    echo "[install] Did the upload finish? Re-sync $BUILD_DIR/ and try again." >&2
    exit 1
fi

require_file "$FUSED_DIR/config.json"

printf '%s\n' "[install] Creating Ollama model..."
ollama create "$MODEL_NAME" -f "$MODELFILE"

printf '%s\n' "[install] Created Ollama model: $MODEL_NAME"
printf '%s\n' "[install] Usage: ollama run $MODEL_NAME \"Your prompt here\""
