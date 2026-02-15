#!/bin/bash
# Simple script to launch the ComfyUI container.

# Ensure basic setup (dependencies, directories) is done
if [ ! -f "setup.sh" ]; then
    echo "Error: setup.sh not found!"
    exit 1
fi

chmod +x setup.sh
./setup.sh

# Start the Docker container
echo "Starting ComfyUI container..."
docker compose up -d --remove-orphans

# Show logs
docker compose logs -f comfyui-production