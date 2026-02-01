#!/bin/bash
# setup_piper.sh (Location: ./v4/lib/)

# 1. Define Paths
PIPER_DIR="./v4/lib/piper"
VOICE_DIR="$PIPER_DIR/voices"
TEMP_DIR="/tmp/piper"

# 2. Define Voice Array [Name|URL]
# Add as many as you like following the pattern "Name|URL"
VOICES=(
    "en_US-ryan-high|https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/high"
    "en_US-lessac-medium|https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium"
)

# Create nested structure
mkdir -p "$VOICE_DIR"

# 3. Download Engine from stable SourceForge Mirror
echo "Downloading Piper Engine (Mirror)..."
wget -L -O piper.tar.gz "https://sourceforge.net/projects/piper-tts.mirror/files/2023.11.14-2/piper_linux_aarch64.tar.gz/download"

if [ $? -ne 0 ]; then
    echo "Download failed. Please check your internet connection."
    exit 1
fi

echo "Extracting Engine..."
mkdir -p "$TEMP_DIR"
tar -xvf piper.tar.gz -C "$TEMP_DIR"
mv "$TEMP_DIR/piper/"* "$PIPER_DIR/"
rm -rf "$TEMP_DIR" piper.tar.gz

# 4. Loop through Voice Array and Download
for entry in "${VOICES[@]}"; do
    # Split the string by the pipe character
    IFS="|" read -r VOICE_NAME VOICE_BASE_URL <<< "$entry"
    
    echo "------------------------------------------------"
    echo "Downloading Voice: $VOICE_NAME"
    wget -L -O "$VOICE_DIR/$VOICE_NAME.onnx" "${VOICE_BASE_URL}/$VOICE_NAME.onnx"
    wget -L -O "$VOICE_DIR/$VOICE_NAME.onnx.json" "${VOICE_BASE_URL}/$VOICE_NAME.onnx.json"
done

# 5. Permissions and Test
PIPER_BIN="$PIPER_DIR/piper"

if [ -f "$PIPER_BIN" ]; then
    chmod +x "$PIPER_BIN"
    echo "------------------------------------------------"
    echo "SUCCESS: Piper bin and voices are in $PIPER_DIR"
    
    # Test with the first voice in the array
    FIRST_VOICE=$(echo "${VOICES[0]}" | cut -d'|' -f1)
    echo "Running test with $FIRST_VOICE..."
    echo "Voice array initialized." | "$PIPER_BIN" --model "$VOICE_DIR/$FIRST_VOICE.onnx" --output_raw | aplay -r 22050 -f S16_LE -t raw
else
    echo "ERROR: Piper binary not found at $PIPER_BIN"
fi