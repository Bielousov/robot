#!/bin/bash
# .v4/lib/ollama/install.sh

# --- CONSTANTS ---
# Use a verified tag. 1b is safe, 4b is fine for Mac Studio.
readonly OLLAMA_VERSION="0.15.6"
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

    echo "[Ollama] Downloading ARM64 binary (v$OLLAMA_VERSION)..."
    wget --continue --tries=5 "https://github.com/ollama/ollama/releases/download/v$OLLAMA_VERSION/ollama-linux-arm64.tar.zst" -O "$OLLAMA_LIB_DIR/ollama.tar.zst"
    sync # FORCE DISK SYNC (Crucial for RPi5 SD cards)
    sleep 5

    echo "[Ollama] Extracting .zst archive..."
    tar --zstd -xf "$OLLAMA_LIB_DIR/ollama.tar.zst" -C "$DIST_DIR" || exit 2
    sync

    # Rewrite files safely
    rsync -a --inplace "$DIST_DIR"/ "$DIST_DIR"/
    sync

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

sleep 5

echo "[Ollama] Creating personality '$CUSTOM_MODEL_NAME'..."
if [ -f "$PERSONALITY_MODEL_FILE" ]; then
    "$OLLAMA_APP" create "$CUSTOM_MODEL_NAME" -f "$PERSONALITY_MODEL_FILE"
else
    echo "[Error] Could not find $PERSONALITY_MODEL_FILE"
fi

kill $OLLAMA_PID
echo "[Ollama] Setup complete!"