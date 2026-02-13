#!/bin/bash
# .v4/lib/ollama/install.sh


LIB_OLLAMA_DIR=$(dirname $(realpath "$0"))
PROJECT_ROOT=$(dirname $(dirname "$LIB_OLLAMA_DIR"))
ENV_FILE="$PROJECT_ROOT/../.env"

DIST_DIR="$LIB_OLLAMA_DIR/dist"
MODELS_DIR="$LIB_OLLAMA_DIR/models"
OLLAMA_BIN="$DIST_DIR/bin/ollama"


if [ -f "$ENV_FILE" ]; then
    echo "[Ollama] Loading config from $ENV_FILE"
    # Extract variables from .env while ignoring comments
    OLLAMA_VERSION=$(grep -v '^#' "$ENV_FILE" | grep 'OLLAMA_VERSION' | cut -d '=' -f2 | tr -d '"' | tr -d "'")
    OLLAMA_MODEL_NAME=$(grep -v '^#' "$ENV_FILE" | grep 'OLLAMA_MODEL_NAME' | cut -d '=' -f2 | tr -d '"' | tr -d "'")
fi

# Fallback defaults if .env is missing or values aren't set
OLLAMA_VERSION=${OLLAMA_VERSION:-"0.15.6"}
OLLAMA_MODEL_NAME=${OLLAMA_MODEL_NAME:-"pip"}

mkdir -p "$DIST_DIR"
mkdir -p "$MODELS_DIR"


# 1. Check if Ollama is already installed in the dist folder
if [[ -f "$OLLAMA_BIN" && -d "$DIST_DIR/lib" ]]; then
    echo "[Ollama] Ollama library already exist. Skipping download."
else
    # Ensure dependencies and clear old processes
    sudo apt-get update && sudo apt-get install -y zstd
    pkill ollama || true

    echo "[Ollama] Downloading ARM64 binary (v$OLLAMA_VERSION)..."
    wget --continue --tries=5 "https://github.com/ollama/ollama/releases/download/v$OLLAMA_VERSION/ollama-linux-arm64.tar.zst" -O "$LIB_OLLAMA_DIR/ollama.tar.zst"
    sync # FORCE DISK SYNC (Crucial for RPi5 SD cards)
    sleep 5

    echo "[Ollama] Extracting .zst archive..."
    tar --zstd -xf "$LIB_OLLAMA_DIR/ollama.tar.zst" -C "$DIST_DIR" || exit 2
    sync

    # Rewrite files safely
    rsync -a --inplace "$DIST_DIR"/ "$DIST_DIR"/
    sync

    rm "$LIB_OLLAMA_DIR/ollama.tar.zst"

    if [ -f "$OLLAMA_BIN" ]; then
        chmod +x "$OLLAMA_BIN"
    fi
fi
