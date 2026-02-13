#!/bin/bash

# Get the directory where THIS script lives (./v4/lib/vosk)
VOSK_LIB_DIR=$(dirname $(realpath "$0"))
PROJECT_ROOT=$(dirname $(dirname "$VOSK_LIB_DIR"))
ENV_FILE="$PROJECT_ROOT/../.env"

# Define destination paths
DIST_DIR="$VOSK_LIB_DIR/dist"
MODELS_DIR="$VOSK_LIB_DIR/models"
VOSK_BIN="$DIST_DIR/vosk"

# Load Environment Variables
if [ -f "$ENV_FILE" ]; then
    source "$ENV_FILE"
    VOSK_MODEL_NAME="${VOSK_MODEL_NAME%$'\r'}"
    VOSK_MODEL_URL="${VOSK_MODEL_URL%$'\r'}"
else
    echo "[Fatal] .env file not found at $ENV_FILE"
    exit 1
fi

mkdir -p "$DIST_DIR"
mkdir -p "$MODELS_DIR"

# 1. Install VOSK Python library into the current virtualenv
if [ ! -d "$VOSK_BIN" ]; then
    echo "------------------------------------------------"
    echo "[Engine] Installing VOSK Python library into $DIST_DIR..."
    
    # Install into dist using pip (inside venv)
    pip install --target="$DIST_DIR" vosk
    
    # Optional: create a marker file
    touch "$VOSK_BIN/.installed"
else
    echo "[Engine] VOSK Python library exists. Skipping."
fi

# 2. Download Model directly to /models
MODEL_DIR="$MODELS_DIR/$VOSK_MODEL_NAME"

if [ -d "$MODEL_DIR" ]; then
    echo "[Model] $VOSK_MODEL_NAME exists. Skipping."
else
    echo "Model path $MODEL_DIR not found..."

    # Ensure dependencies
    sudo apt-get update && sudo apt-get install -y unzip

    echo "------------------------------------------------"
    echo "[Model] Downloading and extracting: $VOSK_MODEL_NAME"

    TEMP_ZIP="$MODELS_DIR/$VOSK_MODEL_NAME.zip"
    wget -q --show-progress -L -O "$TEMP_ZIP" "$VOSK_MODEL_URL"
    sync # FORCE DISK SYNC (Crucial for RPi5 SD cards)
    sleep 5

    # Extract into models folder (strip top-level folder)
    unzip -q "$TEMP_ZIP" -d "$MODELS_DIR"
    rm "$TEMP_ZIP"
    
    mv "$MODELS_DIR/vosk-model-${VOSK_MODEL_NAME#vosk-}" "$MODEL_DIR"
fi

echo "------------------------------------------------"
echo "[Success] VOSK setup complete."
