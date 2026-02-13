#!/bin/bash

# Get the directory where THIS script lives (./v4/lib/piper)
LIB_PIPER_DIR=$(dirname $(realpath "$0"))
PROJECT_ROOT=$(dirname $(dirname "$LIB_PIPER_DIR"))
ENV_FILE="$(dirname "$PROJECT_ROOT")/.env"

# Define destination paths
DIST_DIR="$LIB_PIPER_DIR/dist"
MODELS_DIR="$LIB_PIPER_DIR/models"

# Load Environment Variables
if [ -f "$ENV_FILE" ]; then
    source "$ENV_FILE"
    PIPER_MODEL_NAME="${PIPER_MODEL_NAME%$'\r'}"
    PIPER_MODEL_URL="${PIPER_MODEL_URL%$'\r'}"
else
    echo "[Fatal] .env file not found at $ENV_FILE"
    exit 1
fi

mkdir -p "$DIST_DIR"
mkdir -p "$MODELS_DIR"

# 1. Download Engine directly to /dist
PIPER_BIN="$DIST_DIR/piper"
if [ ! -f "$PIPER_BIN" ]; then
    echo "------------------------------------------------"
    echo "[Engine] Piper binary missing. Downloading to $DIST_DIR..."
    
    # Download directly into dist
    wget -q --show-progress -L -O "$DIST_DIR/piper.tar.gz" "https://sourceforge.net/projects/piper-tts.mirror/files/2023.11.14-2/piper_linux_aarch64.tar.gz/download"
    
    # Extract directly in dist (strip components removes the internal 'piper/' folder layer)
    tar -xf "$DIST_DIR/piper.tar.gz" -C "$DIST_DIR" --strip-components=1
    
    rm "$DIST_DIR/piper.tar.gz"
    chmod +x "$PIPER_BIN"
else
    echo "[Engine] Piper engine exists. Skipping."
fi

# 2. Download Voice model
if [ -z "$PIPER_MODEL_NAME" ] || [ -z "$PIPER_MODEL_URL" ]; then
    echo "[Fatal] PIPER_MODEL_NAME or PIPER_MODEL_URL not set in .env"
    exit 1
fi

ONNX_FILE="$MODELS_DIR/$PIPER_MODEL_NAME.onnx"

if [ -f "$ONNX_FILE" ]; then
    echo "[Voice] $PIPER_MODEL_NAME exists. Skipping."
else
    # Ensure dependencies
    sudo apt-get update && sudo apt-get install -y unzip
    
    echo "------------------------------------------------"
    if [[ "$PIPER_MODEL_URL" == *.zip ]]; then
        echo "[Voice] Downloading and Extracting ZIP: $PIPER_MODEL_NAME"
        
        TEMP_ZIP="$MODELS_DIR/$PIPER_MODEL_NAME.zip"
        wget -q --show-progress -L -O "$TEMP_ZIP" "$PIPER_MODEL_URL"
        unzip -q -j "$TEMP_ZIP" -d "$MODELS_DIR"
        rm "$TEMP_ZIP"
    else
        echo "[Voice] Downloading Files: $PIPER_MODEL_NAME"
        wget -nc -q --show-progress -L -O "$ONNX_FILE" "${PIPER_MODEL_URL}/$PIPER_MODEL_NAME.onnx"
        wget -nc -q --show-progress -L -O "$MODELS_DIR/$PIPER_MODEL_NAME.onnx.json" "${PIPER_MODEL_URL}/$PIPER_MODEL_NAME.onnx.json"
    fi
fi


echo "------------------------------------------------"
echo "[Success] Piper setup complete."