#!/bin/bash

# 1. Resolve Absolute Paths
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
PROJECT_ROOT="$SCRIPT_DIR"
PIPER_DIR="$PROJECT_ROOT/lib/piper"
VOICE_DIR="$PIPER_DIR/voices"
TEMP_DIR="/tmp/piper_install"

echo "[System] Project Root: $PROJECT_ROOT"

# 2. Define Voice Array [Name|URL]
VOICES=(
    # "en_US-bender-medium|https://filedn.com/lUFT01oKaP5FuOR782wnNRm/bender_piper.zip"
    "en_US-danny-low|https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/danny/low"
    "en_US-lessac-medium|https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium"
    "en_US-ryan-high|https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/high"
)

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
    echo "[Engine] Piper binary already exists. Skipping download."
fi

# 4. Loop through Voice Array
for entry in "${VOICES[@]}"; do
    IFS="|" read -r VOICE_NAME VOICE_BASE_URL <<< "$entry"
    
    ONNX_FILE="$VOICE_DIR/$VOICE_NAME.onnx"
    JSON_FILE="$VOICE_DIR/$VOICE_NAME.onnx.json"

    echo "------------------------------------------------"
    if [ -f "$ONNX_FILE" ]; then
        echo "[Voice] $VOICE_NAME already exists. Skipping."
    else
        echo "[Voice] Downloading $VOICE_NAME..."
        # -nc (no-clobber) prevents creating .1, .2 duplicates
        wget -nc -q --show-progress -L -O "$ONNX_FILE" "${VOICE_BASE_URL}/$VOICE_NAME.onnx"
        wget -nc -q --show-progress -L -O "$JSON_FILE" "${VOICE_BASE_URL}/$VOICE_NAME.onnx.json"
    fi
done

# 5. Final Test
if [ -f "$PIPER_BIN" ]; then
    echo "------------------------------------------------"
    echo "[Success] Setup complete."
    echo "Testing audio (en_US-danny-low)..."
    # Testing with mono forced (-c 1) to prevent ALSA buffer hangs
    echo "Audio system online." | "$PIPER_BIN" --model "$VOICE_DIR/en_US-danny-low.onnx" --output_raw | aplay -D plughw:0,0 -r 16000 -f S16_LE -t raw -c 1
fi