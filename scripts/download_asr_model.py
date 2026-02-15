import os
from modelscope import snapshot_download

BASE_DIR = "/home/runner/ComfyUI/models/Qwen2-Audio"
MODEL_ID = "Qwen/Qwen2-Audio-7B-Instruct"

os.makedirs(BASE_DIR, exist_ok=True)
target_path = os.path.join(BASE_DIR, MODEL_ID.split("/")[-1])

if not os.path.exists(target_path):
    print(f"Downloading {MODEL_ID} to {target_path}...")
    try:
        snapshot_download(repo_id=MODEL_ID, local_dir=target_path)
        print("Download complete.")
    except Exception as e:
        print(f"Download failed: {e}")
else:
    print(f"Model already exists at {target_path}")
