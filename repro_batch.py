
import os
import sys
import torch

# Add current dir to path to import app
sys.path.append(os.path.join(os.getcwd(), "qwen_tts_service"))

from app.services.tts_engine import tts_engine
from app.core.config import settings

def test_batch_clone():
    # Ensure a test file exists
    test_ref = "test_ref.wav"
    if not os.path.exists(test_ref):
        print(f"Generating dummy {test_ref}")
        import wave
        import numpy as np
        with wave.open(test_ref, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(24000)
            wf.writeframes((np.random.randn(24000*2) * 32767).astype(np.int16).tobytes())

    print("Running batch clone test...")
    texts = ["This is the first sentence.", "And this is a completely different second sentence."]
    
    # Resolve absolute path for engine
    ref_path = os.path.abspath(test_ref)
    
    try:
        # We need to simulate the environment
        os.environ["DEVICE"] = "cuda:0"
        os.environ["MODEL_ROOT"] = "/app/models/Qwen3-TTS" # This is inside container path, but on host it might differ
        # Actually, let's run this inside the container
        
        results = tts_engine.generate_voice_clone(
            text=texts,
            ref_audio=ref_path,
            ref_text=None,
            language="en"
        )
        
        print(f"Generated {len(results)} audios.")
        
        for i, audio in enumerate(results):
            filename = f"repro_out_{i}.wav"
            with open(filename, "wb") as f:
                f.write(audio)
            print(f"Saved {filename}, size: {len(audio)}")
            
        if len(results) == 2:
            if results[0] == results[1]:
                print("CRITICAL: Both audio outputs are BIT-IDENTICAL!")
            else:
                print("SUCCESS: Audio outputs are different.")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_batch_clone()
