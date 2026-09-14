#!/bin/sh
set -eu

# Registers an already-trained/uploaded Ollama model store (build/$MODEL_NAME/,
# produced by train.sh's isolated `ollama create` and rsynced over) into this
# machine's actual Ollama models directory. Run this on the target machine
# (e.g. the RPi5) after uploading.
#
# This does NOT run `ollama create` - the model was already converted into
# Ollama's content-addressed blob storage on the training machine, so there's
# nothing left to build here, just files to put in the right place. That
# means this script needs no running Ollama server and no `ollama` binary at
# all - it's a plain file copy/merge.

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
SOURCE_STORE="$BUILD_DIR"

# Matches lib/ollama/client.py's MODELS_PATH (OllamaClient sets OLLAMA_MODELS
# to this same directory before spawning its own `ollama serve`), so once
# the blobs/manifest are copied here, the robot's next `ollama serve` start
# finds the model with no further registration step.
TARGET_STORE=${OLLAMA_MODELS:-$PROJECT_ROOT/src/lib/ollama/models}

require_file() {
    if [ ! -e "$1" ]; then
        echo "[install] ERROR: missing $1" >&2
        exit 1
    fi
}

printf '%s\n' "[install] Model name: $MODEL_NAME"
printf '%s\n' "[install] Source store: $SOURCE_STORE"
printf '%s\n' "[install] Target store: $TARGET_STORE"

require_file "$SOURCE_STORE/blobs"
require_file "$SOURCE_STORE/manifests"

MANIFEST="$SOURCE_STORE/manifests/registry.ollama.ai/library/$MODEL_NAME/latest"
if [ ! -e "$MANIFEST" ]; then
    echo "[install] ERROR: missing manifest for '$MODEL_NAME': $MANIFEST" >&2
    echo "[install] Did the upload finish? Re-sync $SOURCE_STORE/ and try again." >&2
    exit 1
fi

if [ -z "$(ls -A "$SOURCE_STORE/blobs" 2>/dev/null)" ]; then
    echo "[install] ERROR: Blob store is empty: $SOURCE_STORE/blobs" >&2
    echo "[install] Did the upload finish? Re-sync $SOURCE_STORE/ and try again." >&2
    exit 1
fi

printf '%s\n' "[install] Registering model blobs..."
mkdir -p "$TARGET_STORE"
cp -R "$SOURCE_STORE/." "$TARGET_STORE/"

printf '%s\n' "[install] Registered model: $MODEL_NAME"
printf '%s\n' "[install] Restart the robot service to pick it up: sudo systemctl restart robot.service"
