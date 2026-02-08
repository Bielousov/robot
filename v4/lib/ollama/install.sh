#!/bin/bash
# .v4/lib/ollama/install.sh

# --- CONSTANTS ---
# Use a verified tag. 1b is safe, 4b is fine for Mac Studio.
readonly BASE_MODEL="gemma3:270m" 
readonly CUSTOM_MODEL_NAME="pip"

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
    wget --continue --tries=5 "https://github.com/ollama/ollama/releases/download/v0.15.5/ollama-linux-arm64.tar.zst" -O "$OLLAMA_LIB_DIR/ollama.tar.zst"

    # FORCE DISK SYNC (Crucial for RPi5 SD cards)
    echo "[Ollama] Flushing buffers to disk..."
    sync
    sleep 1

    echo "[Ollama] Extracting .zst archive..."
    # If tar fails, we'll know immediately
    if ! tar --zstd -xf "$OLLAMA_LIB_DIR/ollama.tar.zst" -C "$DIST_DIR"; then
        echo "[ERROR] Extraction failed. The download was likely corrupt."
        echo "Try deleting $OLLAMA_LIB_DIR/ollama.tar.zst and running again."
        exit 2
    fi

    rm "$OLLAMA_LIB_DIR/ollama.tar.zst"

    if [ -f "$DIST_DIR/bin/ollama" ]; then
        chmod +x "$DIST_DIR/bin/ollama"
        ln -sf "$DIST_DIR/bin/ollama" "$OLLAMA_APP"
    fi
fi


echo "[Ollama] Starting local server..."
export OLLAMA_MODELS="$MODELS_DIR"
# Use the absolute path to start the server
"$OLLAMA_APP" serve > "$DIST_DIR/server.log" 2>&1 &
OLLAMA_PID=$!

# Wait for server to wake up
sleep 1

echo "[Ollama] Pulling $BASE_MODEL..."
"$OLLAMA_APP" pull "$BASE_MODEL"

echo "[Ollama] Creating personality '$CUSTOM_MODEL_NAME'..."
if [ -f "$PERSONALITY_MODEL_FILE" ]; then
    "$OLLAMA_APP" create "$CUSTOM_MODEL_NAME" -f "$PERSONALITY_MODEL_FILE"
else
    echo "[Error] Could not find $PERSONALITY_MODEL_FILE"
fi

kill $OLLAMA_PID
echo "[Ollama] Setup complete!"