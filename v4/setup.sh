#!/bin/bash
# Run this script while inside your ./v4/lib/ directory

# 1. Create nested structure relative to current folder
mkdir -p piper/voices

# 2. Download Engine (Using the direct 1.2.0 link with redirect support)
echo "Downloading Piper Engine..."
# Added -L to follow redirects and used the direct release asset link
wget -L -O piper.tar.gz "https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_linux_aarch64.tar.gz"

# Check if download actually worked before extracting
if [ s$? -ne 0 ]; then
    echo "Download failed. GitHub might be down or the link has moved."
    exit 1
fi

tar -xvf piper.tar.gz -C ./piper --strip-components=1
rm piper.tar.gz

# 3. Download Voices into the new voices subfolder
echo "Downloading Voice Model from Hugging Face..."
# Hugging Face links MUST have -L to follow the redirect to the storage server
VOICE_URL="https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium"

wget -L -O ./piper/voices/en_US-lessac-medium.onnx "${VOICE_URL}/en_US-lessac-medium.onnx"
wget -L -O ./piper/voices/en_US-lessac-medium.onnx.json "${VOICE_URL}/en_US-lessac-medium.onnx.json"

# 4. Finalize
if [ -f "./piper/piper" ]; then
    chmod +x ./piper/piper
    echo "------------------------------------------------"
    echo "Installation complete. Piper bin and voices are in ./lib/piper/"
    echo "Try a test command:"
    echo "echo 'System online' | ./piper/piper --model ./piper/voices/en_US-lessac-medium.onnx --output_raw | aplay -r 22050 -f S16_LE -t raw"
else
    echo "Error: Piper binary not found in ./piper/ after extraction."
fi