#!/bin/bash
# ./lib/ollama/install.sh


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
OLLAMA_VERSION=${OLLAMA_VERSION:-"0.33.1"}
OLLAMA_MODEL_NAME=${OLLAMA_MODEL_NAME:-"pip"}
OLLAMA_RELEASE_VERSION=${OLLAMA_VERSION%%-*}

mkdir -p "$DIST_DIR"
mkdir -p "$MODELS_DIR"


# 1. Check whether the installed binary matches the requested version
installed_version=""
if [[ -x "$OLLAMA_BIN" && -d "$DIST_DIR/lib" ]]; then
    installed_version=$("$OLLAMA_BIN" --version 2>/dev/null | sed -nE 's/.*([0-9]+\.[0-9]+\.[0-9]+).*/\1/p')
fi

if [[ "$installed_version" == "$OLLAMA_RELEASE_VERSION" ]]; then
    echo "[Ollama] Ollama $OLLAMA_VERSION is already installed. Skipping download."
else
    if [[ -n "$installed_version" ]]; then
        echo "[Ollama] Replacing Ollama $installed_version with $OLLAMA_VERSION..."
    else
        echo "[Ollama] Installing Ollama $OLLAMA_VERSION..."
    fi

    # Ensure dependencies and clear old processes
    sudo apt-get update && sudo apt-get install -y zstd
    pkill ollama || true

    echo "[Ollama] Downloading ARM64 binary (v$OLLAMA_VERSION)..."
    rm -f "$LIB_OLLAMA_DIR/ollama.tar.zst"
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
