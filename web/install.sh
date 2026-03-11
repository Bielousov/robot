#!/bin/bash

# Install script for web dependencies
# Downloads React, ReactDOM, and Babel to local dist folder

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIST_DIR="$SCRIPT_DIR/dist"

mkdir -p "$DIST_DIR"

echo "[Web] Downloading dependencies to $DIST_DIR..."

# React 18 production build
echo "[Web] Downloading React 18..."
wget -q -O "$DIST_DIR/react.production.min.js" \
    "https://unpkg.com/react@18/umd/react.production.min.js" || \
    curl -s -o "$DIST_DIR/react.production.min.js" \
    "https://unpkg.com/react@18/umd/react.production.min.js"

# ReactDOM 18 production build
echo "[Web] Downloading ReactDOM 18..."
wget -q -O "$DIST_DIR/react-dom.production.min.js" \
    "https://unpkg.com/react-dom@18/umd/react-dom.production.min.js" || \
    curl -s -o "$DIST_DIR/react-dom.production.min.js" \
    "https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"

# Babel Standalone
echo "[Web] Downloading Babel Standalone..."
wget -q -O "$DIST_DIR/babel.min.js" \
    "https://unpkg.com/@babel/standalone/babel.min.js" || \
    curl -s -o "$DIST_DIR/babel.min.js" \
    "https://unpkg.com/@babel/standalone/babel.min.js"

# Verify downloads
echo "[Web] Verifying downloads..."
if [[ -f "$DIST_DIR/react.production.min.js" ]]; then
    SIZE=$(wc -c < "$DIST_DIR/react.production.min.js")
    echo "✓ React: $(($SIZE / 1024)) KB"
else
    echo "✗ Failed to download React"
    exit 1
fi

if [[ -f "$DIST_DIR/react-dom.production.min.js" ]]; then
    SIZE=$(wc -c < "$DIST_DIR/react-dom.production.min.js")
    echo "✓ ReactDOM: $(($SIZE / 1024)) KB"
else
    echo "✗ Failed to download ReactDOM"
    exit 1
fi

if [[ -f "$DIST_DIR/babel.min.js" ]]; then
    SIZE=$(wc -c < "$DIST_DIR/babel.min.js")
    echo "✓ Babel: $(($SIZE / 1024)) KB"
else
    echo "✗ Failed to download Babel"
    exit 1
fi

echo "[Web] ✓ All dependencies installed successfully"
