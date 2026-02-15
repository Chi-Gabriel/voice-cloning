#!/bin/bash
echo "Running pre-start script..."

# 1. Symlink custom nodes
if [ -d "/comfyui/custom_nodes/ComfyUI-Qwen3-TTS" ]; then
    echo "Linking ComfyUI-Qwen3-TTS custom node..."
    ln -sfn /comfyui/custom_nodes/ComfyUI-Qwen3-TTS /home/runner/ComfyUI/custom_nodes/ComfyUI-Qwen3-TTS
fi

if [ -d "/comfyui/custom_nodes/ComfyUI-Qwen3-ASR" ]; then
    echo "Linking ComfyUI-Qwen3-ASR custom node..."
    ln -sfn /comfyui/custom_nodes/ComfyUI-Qwen3-ASR /home/runner/ComfyUI/custom_nodes/ComfyUI-Qwen3-ASR
fi

# 2. Symlink models folder & Auto-Download Models
if [ -d "/comfyui/models/Qwen3-TTS" ]; then
    echo "Linking Qwen3-TTS models..."
    mkdir -p /home/runner/ComfyUI/models/Qwen3-TTS
    # Check if TTS models exist, otherwise download (Run ONCE)
    if [ -z "$(ls -A /comfyui/models/Qwen3-TTS)" ]; then
        echo "TTS Model directory empty. Triggering download..."
        python3 /home/runner/scripts/download_tts.py
    fi
    ln -sfn /comfyui/models/Qwen3-TTS/* /home/runner/ComfyUI/models/Qwen3-TTS/
fi

# 3. Symlink ASR model (Important for the workflow)
if [ -d "/comfyui/models/Qwen3-ASR" ]; then
     echo "Linking Qwen3-ASR models..."
     mkdir -p /home/runner/ComfyUI/models/Qwen3-ASR
     # Check if ASR models exist, otherwise download (Run ONCE)
     if [ -z "$(ls -A /comfyui/models/Qwen3-ASR)" ]; then
         echo "ASR Model directory empty. Triggering download..."
         python3 /home/runner/scripts/download_asr.py
     fi
     ln -sfn /comfyui/models/Qwen3-ASR/* /home/runner/ComfyUI/models/Qwen3-ASR/
fi

# 4. Install requirements - The core "Run Once" setup
# We install transformers first, then the Qwen packages which might conflict
pip install comfy-aimdo bitsandbytes accel-brain-base accelerate sentencepiece scipy soundfile torchaudio
pip install transformers==4.57.3
pip install qwen-tts
# qwen-asr is strict about transformers version, so we install it with --no-deps to force it to use our version
pip install qwen-asr --no-deps

# 5. Install Flash Attention (Local Pre-built wheel)
# We downloaded this to /scripts/, which is mounted at /home/runner/scripts/
pip install /home/runner/scripts/flash_attn-2.7.2.post1+cu12torch2.5cxx11abiFALSE-cp311-cp311-linux_x86_64.whl || echo "Flash Attention install failed, dragging on..."

# 6. Install node-specific requirements if they exist
if [ -f "/home/runner/ComfyUI/custom_nodes/ComfyUI-Qwen3-TTS/requirements.txt" ]; then
    pip install -r /home/runner/ComfyUI/custom_nodes/ComfyUI-Qwen3-TTS/requirements.txt
fi

# Ensure the user site-packages is in the PYTHONPATH
USER_SITE=$(python3 -m site --user-site)
export PYTHONPATH="${PYTHONPATH}:${USER_SITE}"
echo "PYTHONPATH set to: ${PYTHONPATH}"
