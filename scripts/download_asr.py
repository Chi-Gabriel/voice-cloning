import os
from huggingface_hub import snapshot_download

# The exact repo ID the node is looking for
REPO_ID = "Qwen/Qwen3-ASR-1.7B"
# The path the node expects (based on the error message)
TARGET_DIR = "/comfyui/models/Qwen3-ASR/Qwen3-ASR-1.7B"

print(f"Downloading {REPO_ID} to {TARGET_DIR}...")
try:
    snapshot_download(repo_id=REPO_ID, local_dir=TARGET_DIR, resume_download=True)
    print("Download complete.")
except Exception as e:
    print(f"Download failed: {e}")
