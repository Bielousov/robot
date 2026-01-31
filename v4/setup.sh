#!/bin/bash
# setup_piper.sh (run inside ./v4/lib/)

# 1. Create nested structure
mkdir -p piper/voices

# 2. Download Engine
echo "Downloading Piper Engine..."
wget -O piper.tar.gz https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_linux_aarch64.tar.gz
tar -xvf piper.tar.gz -C ./piper --strip-components=1
rm piper.tar.gz

# 3. Download Voices into the new voices subfolder
echo "Downloading Voice Model..."
VOICE_URL="https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium"
wget -O ./piper/voices/en_US-lessac-medium.onnx "${VOICE_URL}/en_US-lessac-medium.onnx"
wget -O ./piper/voices/en_US-lessac-medium.onnx.json "${VOICE_URL}/en_US-lessac-medium.onnx.json"

chmod +x ./piper/piper
echo "Installation complete. Piper bin and voices are in ./lib/piper/"