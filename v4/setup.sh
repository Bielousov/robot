#!/bin/bash

# 1. Resolve Absolute Paths
# SCRIPT_DIR is /home/pip/projects/robot/v4/
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
PROJECT_ROOT="$SCRIPT_DIR"

# ENV_FILE is now expected in the parent directory of v4/
# i.e., /home/pip/projects/robot/.env
ENV_FILE="$(dirname "$SCRIPT_DIR")/.env"

PIPER_DIR="$PROJECT_ROOT/lib/piper"
VOICE_DIR="$PIPER_DIR/voices"
TEMP_DIR="/tmp/piper_install"

echo "[System] Script Path: $SCRIPT_DIR"
echo "[System] Searching for .env at: $ENV_FILE"

# 2. Load and Clean Environment Variables
if [ -f "$ENV_FILE" ]; then
    echo "[System] .env found. Loading voices..."
    # Export variables from .env while ignoring comments
    export $(grep -v '^#' "$ENV_FILE" | xargs -d '\n')
    
    # Cleaning: Handle multi-line PIPER_VOICES from .env
    PIPER_VOICES=$(echo "$PIPER_VOICES" | tr -d '\r' | tr '\n' ' ' | tr -s ' ')
else
    echo "[Fatal] .env file not found at $ENV_FILE"
    exit 1
fi

if [ -z "$PIPER_VOICES" ]; then
    echo "[Error] PIPER_VOICES is empty or not defined in .env"
    exit 1
fi

mkdir -p "$VOICE_DIR"

# 3. Download Engine (Only if binary is missing)
PIPER_BIN="$PIPER_DIR/piper"
if [ ! -f "$PIPER_BIN" ]; then
    echo "------------------------------------------------"
    echo "[Engine] Piper binary not found. Downloading..."
    # Use aarch64 for RPi 5
    wget -q --show-progress -L -O piper.tar.gz "https://sourceforge.net/projects/piper-tts.mirror/files/2023.11.14-2/piper_linux_aarch64.tar.gz/download"
    
    mkdir -p "$TEMP_DIR"
    tar -xf piper.tar.gz -C "$TEMP_DIR"
    mv "$TEMP_DIR/piper/"* "$PIPER_DIR/"
    rm -rf "$TEMP_DIR" piper.tar.gz
    chmod +x "$PIPER_BIN"
    echo "[Engine] Piper engine installed."
else
    echo "[Engine] Piper engine already exists. Skipping."
fi

# 4. Loop through Voice List
for entry in $PIPER_VOICES; do
    [ -z "$entry" ] && continue

    IFS="|" read -r VOICE_NAME VOICE_BASE_URL <<< "$entry"
    ONNX_FILE="$VOICE_DIR/$VOICE_NAME.onnx"
    
    echo "------------------------------------------------"
    if [ -f "$ONNX_FILE" ]; then
        echo "[Voice] $VOICE_NAME already exists. Skipping."
        continue
    fi

    if [[ "$VOICE_BASE_URL" == *.zip ]]; then
        echo "[Voice] Downloading ZIP: $VOICE_NAME"
        ZIP_PATH="/tmp/$VOICE_NAME.zip"
        EXTRACT_DIR="/tmp/extract_$VOICE_NAME"
        
        wget -q --show-progress -L -O "$ZIP_PATH" "$VOICE_BASE_URL"
        
        mkdir -p "$EXTRACT_DIR"
        unzip -q -j "$ZIP_PATH" -d "$EXTRACT_DIR"
        
        mv "$EXTRACT_DIR"/*.onnx "$VOICE_DIR/" 2>/dev/null
        mv "$EXTRACT_DIR"/*.json "$VOICE_DIR/" 2>/dev/null
        
        rm -rf "$ZIP_PATH" "$EXTRACT_DIR"
    else
        echo "[Voice] Downloading Files: $VOICE_NAME"
        wget -nc -q --show-progress -L -O "$VOICE_DIR/$VOICE_NAME.onnx" "${VOICE_BASE_URL}/$VOICE_NAME.onnx"
        wget -nc -q --show-progress -L -O "$VOICE_DIR/$VOICE_NAME.onnx.json" "${VOICE_BASE_URL}/$VOICE_NAME.onnx.json"
    fi
done

echo "------------------------------------------------"
echo "[Success] Piper setup is complete."