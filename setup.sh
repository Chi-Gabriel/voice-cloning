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
mkdir -p storage/workflows

# 3. Clone correct Custom Nodes (FlyBird for TTS, DarioFT for ASR)
TTS_NODE_DIR="storage/custom_nodes/ComfyUI-Qwen-TTS"
ASR_NODE_DIR="storage/custom_nodes/ComfyUI-Qwen3-ASR"

if [ ! -d "$TTS_NODE_DIR" ]; then
    echo "Cloning FlyBird TTS Nodes..."
    git clone https://github.com/flybirdxx/ComfyUI-Qwen-TTS.git "$TTS_NODE_DIR"
    # Copy official example workflows to our workflows folder for easy access
    cp "$TTS_NODE_DIR"/example_workflows/*.json storage/workflows/ 2>/dev/null || true
else
    echo "FlyBird TTS Nodes already present."
fi

if [ ! -d "$ASR_NODE_DIR" ]; then
    echo "Cloning DarioFT ASR Nodes..."
    git clone https://github.com/DarioFT/ComfyUI-Qwen3-ASR.git "$ASR_NODE_DIR"
else
    echo "DarioFT ASR Nodes already present."
fi

echo "Setup complete. Run ./start.sh to launch ComfyUI."
