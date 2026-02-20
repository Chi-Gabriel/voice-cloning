import os
import torch
import torchaudio
import time
from pyannote.audio import Pipeline

# Inside container, env vars are passed by docker-compose
HF_TOKEN = os.getenv("HF_TOKEN")
# Audio file is mapped to /tmp/tts_files
AUDIO_FILE = "/tmp/tts_files/8b996d83-eb8b-458d-af2c-abbc3b2ee475.wav"

def test_diarization():
    if not HF_TOKEN:
        print("ERROR: HF_TOKEN environment variable not set in container")
        return

    print(f"Loading diarization pipeline with token: {HF_TOKEN[:8]}...")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    try:
        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=HF_TOKEN
        )
        pipeline.to(device)
        print("Pipeline loaded successfully.")

        if not os.path.exists(AUDIO_FILE):
             print(f"ERROR: Audio file not found at {AUDIO_FILE}")
             # Check if it exists with .wav
             return

        print(f"Processing audio: {AUDIO_FILE}...")
        t0 = time.perf_counter()
        
        # Optimized loading
        waveform, sample_rate = torchaudio.load(AUDIO_FILE)
        if waveform.shape[0] > 1:
            waveform = waveform.mean(dim=0, keepdim=True)
        waveform = waveform.to(device)

        diarization = pipeline({"waveform": waveform, "sample_rate": sample_rate})
        
        dur = time.perf_counter() - t0
        print(f"Diarization complete in {dur:.2f}s")

        for turn, _, speaker in diarization.itertracks(yield_label=True):
            print(f"start={turn.start:.1f}s stop={turn.end:.1f}s speaker_{speaker}")

    except Exception as e:
        print(f"Error during diarization: {e}")

if __name__ == "__main__":
    test_diarization()
