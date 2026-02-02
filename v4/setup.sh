#!/bin/bash

# 1. Resolve Absolute Paths
# Ensures script works from project root or /v4 folder
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
PROJECT_ROOT="$SCRIPT_DIR"
PIPER_DIR="$PROJECT_ROOT/lib/piper"
VOICE_DIR="$PIPER_DIR/voices"
ENV_FILE="$PROJECT_ROOT/.env"
TEMP_DIR="/tmp/piper_install"

echo "[System] Project Root detected: $PROJECT_ROOT"

# 2. Load and Clean Environment Variables
if [ -f "$ENV_FILE" ]; then
    echo "[System] Loading voices from .env..."
    # Export variables from .env while ignoring comments
    export $(grep -v '^#' "$ENV_FILE" | xargs -d '\n')
    
    # Cleaning Logic: Convert multi-line PIPER_VOICES into a clean space-separated list
    # tr -d '\r' handles Windows line endings; tr '\n' ' ' collapses lines into one string
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
# Because we cleaned the string, the 'for' loop now correctly sees spaces as delimiters
for entry in $PIPER_VOICES; do
    # Skip empty entries that might result from trailing backslashes
    [ -z "$entry" ] && continue

    IFS="|" read -r VOICE_NAME VOICE_BASE_URL <<< "$entry"
    
    ONNX_FILE="$VOICE_DIR/$VOICE_NAME.onnx"
    
    echo "------------------------------------------------"
    if [ -f "$ONNX_FILE" ]; then
        echo "[Voice] $VOICE_NAME already exists. Skipping."
        continue
    fi

    # Branch Logic: ZIP vs Standard File
    if [[ "$VOICE_BASE_URL" == *.zip ]]; then
        echo "[Voice] Downloading ZIP: $VOICE_NAME"
        ZIP_PATH="/tmp/$VOICE_NAME.zip"
        EXTRACT_DIR="/tmp/extract_$VOICE_NAME"
        
        wget -q --show-progress -L -O "$ZIP_PATH" "$VOICE_BASE_URL"
        
        mkdir -p "$EXTRACT_DIR"
        # -j (junk paths) flattens the internal folder structure
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
echo "[Success] Piper setup is complete and stable."