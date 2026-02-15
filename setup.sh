#!/bin/bash
# Checks for dependencies and downloads necessary files to ensure reproducibility.

# 1. Download Flash Attention Wheel (Pre-built binary for speed)
WHEEL_URL="https://github.com/Dao-AILab/flash-attention/releases/download/v2.7.2.post1/flash_attn-2.7.2.post1+cu12torch2.5cxx11abiFALSE-cp311-cp311-linux_x86_64.whl"
WHEEL_FILE="scripts/flash_attn-2.7.2.post1+cu12torch2.5cxx11abiFALSE-cp311-cp311-linux_x86_64.whl"

if [ ! -f "$WHEEL_FILE" ]; then
    echo "Downloading Flash Attention wheel..."
    wget -O "$WHEEL_FILE" "$WHEEL_URL"
    if [ $? -eq 0 ]; then
        echo "Download successful."
    else
        echo "Download failed. Please check your internet connection."
        exit 1
    fi
else
    echo "Flash Attention wheel already present."
fi

# 2. Create directory structure for persistent storage
mkdir -p storage/models
mkdir -p storage/output
mkdir -p storage/user
mkdir -p storage/custom_nodes

echo "Setup complete. Run ./start.sh to launch ComfyUI."
