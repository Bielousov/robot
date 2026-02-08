#!/bin/bash
# .v4/lib/ollama/install.sh

OLLAMA_LIB_DIR=$(dirname $(realpath "$0"))
PROJECT_ROOT=$(dirname $(dirname "$OLLAMA_LIB_DIR"))

DIST_DIR="$OLLAMA_LIB_DIR/dist"
MODELS_DIR="$OLLAMA_LIB_DIR/models"
# We update this to point exactly where the binary will end up
OLLAMA_APP="$DIST_DIR/ollama"
PERSONALITY_MODEL_FILE="$PROJECT_ROOT/pip.modelfile"

mkdir -p "$DIST_DIR"
mkdir -p "$MODELS_DIR"

# 1. Check if Ollama is already installed in the dist folder
if [[ -d "$DIST_DIR/bin" && -d "$DIST_DIR/lib" ]]; then
    echo "[Ollama] dist/bin and dist/lib already exist. Skipping download."
else
    # Ensure dependencies and clear old processes
    sudo apt-get update && sudo apt-get install -y zstd
    pkill ollama || true

    echo "[Ollama] Downloading verified ARM64 binary (v0.15.5)..."
    wget "https://github.com/ollama/ollama/releases/download/v0.15.5/ollama-linux-arm64.tar.zst" -O "$OLLAMA_LIB_DIR/ollama.tar.zst"

    echo "[Ollama] Extracting .zst archive..."
    # --zstd flag for tar extracts the bin and lib folders into DIST_DIR
    tar --zstd -xf "$OLLAMA_LIB_DIR/ollama.tar.zst" -C "$DIST_DIR"
    rm "$OLLAMA_LIB_DIR/ollama.tar.zst"

    # Set permissions for the binary
    if [ -f "$DIST_DIR/bin/ollama" ]; then
        chmod +x "$DIST_DIR/bin/ollama"
        # Create a symlink in the root of dist for easier access
        ln -sf "$DIST_DIR/bin/ollama" "$OLLAMA_APP"
    fi
fi

echo "[Ollama] Starting local server..."
export OLLAMA_MODELS="$MODELS_DIR"
# Use the absolute path to start the server
"$OLLAMA_APP" serve > "$DIST_DIR/server.log" 2>&1 &
OLLAMA_PID=$!

# Wait for server to wake up
sleep 5

echo "[Ollama] Pulling Gemma 3 1B..."
"$OLLAMA_APP" pull gemma3:1b

echo "[Ollama] Creating personality 'pip'..."
if [ -f "$PERSONALITY_MODEL_FILE" ]; then
    "$OLLAMA_APP" create pip -f "$PERSONALITY_MODEL_FILE"
else
    echo "[Error] Could not find $PERSONALITY_MODEL_FILE"
fi

kill $OLLAMA_PID
echo "[Ollama] Setup complete!"