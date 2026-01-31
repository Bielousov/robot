#!/bin/bash
# setup_piper.sh

# 1. Create folders
mkdir -p lib/piper
mkdir -p lib/voices

# 2. Download and extract Piper into the local folder
wget -qO- https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_linux_aarch64.tar.gz | tar xvz -C ./lib/piper --strip-components=1

# 3. Get the voice
wget -P ./lib/voices/ https://github.com/rhasspy/piper/releases/download/v1.2.0/en_US-lessac-medium.onnx
wget -P ./lib/voices/ https://github.com/rhasspy/piper/releases/download/v1.2.0/en_US-lessac-medium.onnx.json

echo "Piper dependency installed locally in project folder."