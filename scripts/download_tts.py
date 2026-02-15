import os
from huggingface_hub import snapshot_download

MODELS = {
    "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice": "Qwen3-TTS-12Hz-1.7B-CustomVoice",
    "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign": "Qwen3-TTS-12Hz-1.7B-VoiceDesign",
    "Qwen/Qwen3-TTS-12Hz-1.7B-Base": "Qwen3-TTS-12Hz-1.7B-Base",
    "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice": "Qwen3-TTS-12Hz-0.6B-CustomVoice",
    "Qwen/Qwen3-TTS-12Hz-0.6B-Base": "Qwen3-TTS-12Hz-0.6B-Base",
    "Qwen/Qwen3-TTS-Tokenizer-12Hz": "Qwen3-TTS-Tokenizer-12Hz",
}

BASE_DIR = "/comfyui/models/Qwen3-TTS"
os.makedirs(BASE_DIR, exist_ok=True)

for repo_id, folder_name in MODELS.items():
    target_path = os.path.join(BASE_DIR, folder_name)
    if os.path.exists(target_path) and os.listdir(target_path):
        print(f"Skipping {repo_id}, already exists at {target_path}")
        continue
    
    print(f"Downloading {repo_id} to {target_path}...")
    try:
        snapshot_download(repo_id=repo_id, local_dir=target_path)
        print(f"Successfully downloaded {repo_id}")
    except Exception as e:
        print(f"Failed to download {repo_id}: {e}")

print("All downloads finished.")
