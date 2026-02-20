# Speaker Diarization Implementation

This feature integrates speaker diarization into the Qwen-TTS Studio using the `pyannote/speaker-diarization-3.1` model. It follows the same architectural patterns as the ASR and TTS services for consistency and GPU efficiency.

## Files Involved

- [diarization_models.py](file:///home/user/voice-clone/qwen_tts_service/app/models/diarization_models.py): Defines Pydantic models for diarization requests and responses.
- [diarization_engine.py](file:///home/user/voice-clone/qwen_tts_service/app/services/diarization_engine.py): Core singleton service managing the pyannote pipeline.
- [diarization.py](file:///home/user/voice-clone/qwen_tts_service/app/api/v1/endpoints/diarization.py): REST endpoints for synchronous diarization.
- [gpu_worker.py](file:///home/user/voice-clone/qwen_tts_service/app/services/gpu_worker.py): Integrates diarization into the async batch queue.
- [queue_models.py](file:///home/user/voice-clone/qwen_tts_service/app/models/queue_models.py): Added `diarize` operation and speaker hint parameters.
- [main.py](file:///home/user/voice-clone/qwen_tts_service/app/main.py): Registers the diarization router.
- [config.py](file:///home/user/voice-clone/qwen_tts_service/app/core/config.py): Configuration settings for the diarization model and HF token.

## Logic & Algorithm

### 1. Lazy Loading & Model Management
The diarization engine is a singleton that registers with the `ModelManager`. It only loads the `pyannote` pipeline into VRAM when a request is made. If another model (TTS or ASR) is active, the `ModelManager` unloads it first to prevent OOM errors.

### 2. High-Speed Inference Optimization
To achieve "faster-than-realtime" performance, the implementation uses two key speedups:
- **Waveform Pre-loading**: Instead of passing file paths to `pyannote` (which uses slow internal I/O), audio is loaded once using `torchaudio` on the CPU/RAM and passed to the pipeline as a memory tensor. This results in a ~3x speedup for short audio files.
- **Sticky Scheduling**: In the async queue, the `GPUWorker` prioritizes consecutive diarization tasks to keep the model warm in VRAM and avoid expensive model swap overhead.

### 3. Queue Support
Diarization is natively supported in the async queue by setting `operation: "diarize"`. Results are saved as JSON files in the file store, identical to transcription results.

## Configuration

Diarization requires a HuggingFace Hub token for the gated `pyannote/speaker-diarization-3.1` model.
- Set `HF_TOKEN` in the environment or `.env` file.
- `ENABLE_DIARIZATION`: Toggle the feature on/off.
- `DIARIZATION_MAX_BATCH_SIZE`: Limits the number of concurrent diarization tasks in a GPU worker batch.

## External API Consumption

To consume the diarization service from an external server, use the following specifications.

### Authentication
All requests require the `x-api-key` header configured in your `.env` file.

### 1. Upload & Diarize (Direct)
**Endpoint**: `POST /api/v1/diarize/file`  
**Content-Type**: `multipart/form-data`

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `audio` | File | Yes | The audio file to process |
| `num_speakers` | int | No | Exact number of speakers (if known) |
| `min_speakers` | int | No | Minimum expected speakers |
| `max_speakers` | int | No | Maximum expected speakers |

**Example (cURL)**:
```bash
curl -X POST "https://your-server.com/api/v1/diarize/file" \
     -H "x-api-key: YOUR_API_KEY" \
     -F "audio=@/path/to/audio.wav" \
     -F "min_speakers=1" \
     -F "max_speakers=5"
```

### 2. Response Format
The API returns a JSON object containing identified speaker segments.

```json
{
  "segments": [
    {
      "speaker": "SPEAKER_00",
      "start": 0.12,
      "end": 4.56
    },
    {
      "speaker": "SPEAKER_01",
      "start": 5.10,
      "end": 10.20
    }
  ],
  "num_speakers": 2,
  "performance": 1.25
}
```

### Python Example (Requests)
```python
import requests

url = "https://your-server.com/api/v1/diarize/file"
headers = {"x-api-key": "YOUR_API_KEY"}
files = {"audio": open("interview.mp3", "rb")}
data = {"min_speakers": 1, "max_speakers": 10}

response = requests.post(url, headers=headers, files=files, data=data)
result = response.json()

for segment in result["segments"]:
    print(f"[{segment['start']:.2f}s - {segment['end']:.2f}s] {segment['speaker']}")
```
