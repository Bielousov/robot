#!/bin/bash

# Get the directory where THIS script lives (./v4/lib/piper)
LIB_PIPER_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)

# Define destination paths
DIST_DIR="$LIB_PIPER_DIR/dist"
MODELS_DIR="$LIB_PIPER_DIR/models"

# Path Logic to find .env
PROJECT_ROOT=$(dirname $(dirname "$LIB_PIPER_DIR"))
ENV_FILE="$(dirname "$PROJECT_ROOT")/.env"

# Load Environment Variables
if [ -f "$ENV_FILE" ]; then
    source "$ENV_FILE"
    PIPER_VOICES=$(echo $PIPER_VOICES | tr -d '\r')
else
    echo "[Fatal] .env file not found at $ENV_FILE"
    exit 1
fi

mkdir -p "$MODELS_DIR"
mkdir -p "$DIST_DIR"

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

# 2. Download Voices directly to /models
for entry in $PIPER_VOICES; do
    [ -z "$entry" ] && continue
    IFS="|" read -r VOICE_NAME VOICE_BASE_URL <<< "$entry"
    ONNX_FILE="$MODELS_DIR/$VOICE_NAME.onnx"
    
    if [ -f "$ONNX_FILE" ]; then
        echo "[Voice] $VOICE_NAME exists. Skipping."
        continue
    fi

    echo "------------------------------------------------"
    if [[ "$VOICE_BASE_URL" == *.zip ]]; then
        echo "[Voice] Downloading and Extracting ZIP: $VOICE_NAME"
        
        # Download ZIP to voices folder
        TEMP_ZIP="$MODELS_DIR/$VOICE_NAME.zip"
        wget -q --show-progress -L -O "$TEMP_ZIP" "$VOICE_BASE_URL"
        
        # Unzip directly into voices folder (junking paths to keep it flat)
        unzip -q -j "$TEMP_ZIP" -d "$MODELS_DIR"
        
        rm "$TEMP_ZIP"
    else
        echo "[Voice] Downloading Files: $VOICE_NAME"
        wget -nc -q --show-progress -L -O "$MODELS_DIR/$VOICE_NAME.onnx" "${VOICE_BASE_URL}/$VOICE_NAME.onnx"
        wget -nc -q --show-progress -L -O "$MODELS_DIR/$VOICE_NAME.onnx.json" "${VOICE_BASE_URL}/$VOICE_NAME.onnx.json"
    fi
done

echo "------------------------------------------------"
echo "[Success] Piper setup complete."