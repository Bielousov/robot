#!/bin/bash
# setup_piper.sh (Location: ./v4/lib/)

# 1. Define Paths
PIPER_DIR="./v4/lib/piper"
VOICE_DIR="$PIPER_DIR/voices"
TEMP_DIR="/tmp"

# Create nested structure
mkdir -p "$VOICE_DIR"

# 2. Download Engine from stable SourceForge Mirror
echo "Downloading Piper Engine (Mirror)..."
# -L follows redirects, -O saves it as piper.tar.gz
wget -L -O piper.tar.gz "https://sourceforge.net/projects/piper-tts.mirror/files/2023.11.14-2/piper_linux_aarch64.tar.gz/download"

# Check if download was successful
if [ $? -ne 0 ]; then
    echo "Download failed. Please check your internet connection."
    exit 1
fi

echo "Extracting..."
# Create a temporary folder to avoid "piper/piper/piper" issues
mkdir -p "$TEMP_DIR"
tar -xvf piper.tar.gz -C "$TEMP_DIR"

# Move the actual contents to our piper folder
# The tar usually contains a folder named 'piper', we want its contents
mv "$TEMP_DIR/piper/"* "$PIPER_DIR/"

# Cleanup
rm -rf "$TEMP_DIR" piper.tar.gz

# 3. Voice Model
echo "Ensuring Voice Model is in $VOICE_DIR/..."
VOICE_URL="https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium"

wget -L -O "$VOICE_DIR/en_US-lessac-medium.onnx" "${VOICE_URL}/en_US-lessac-medium.onnx"
wget -L -O "$VOICE_DIR/en_US-lessac-medium.onnx.json" "${VOICE_URL}/en_US-lessac-medium.onnx.json"

# 4. Permissions
PIPER_BIN="$PIPER_DIR/piper"

if [ -f "$PIPER_BIN" ]; then
    chmod +x "$PIPER_BIN"
    echo "------------------------------------------------"
    echo "SUCCESS: Piper bin and voices are in $PIPER_DIR"
    echo "Running test..."
    echo "Test successful." | "$PIPER_BIN" --model "$VOICE_DIR/en_US-lessac-medium.onnx" --output_raw | aplay -r 22050 -f S16_LE -t raw
else
    echo "ERROR: Piper binary not found. Listing folder contents for debug:"
    ls -R "$PIPER_DIR"
fi