# Qwen-TTS Backend Architecture

## Overview
This backend service provides a high-performance REST API for Qwen3-TTS models, supporting:
1.  **Voice Design**: Generating speech from text descriptions.
2.  **Voice Cloning**: Cloning voices from reference audio.
3.  **Custom Voice**: Using pre-defined high-quality speaker profiles.

## Architecture Guidelines
-   **Model Management**: The `TTSEngine` singleton manages model lifecycles to optimize VRAM usage.
-   **Lazy Loading**: To prevent startup OOM errors (especially when running alongside ComfyUI), models are initialized and loaded into GPU memory only on their first request. This keeps the API responsive even if global GPU memory is tight.
-   **Batch Processing**: All endpoints support batch requests. By passing lists of inputs, the service leverages the underlying model's batch inference capabilities for maximum GPU throughput.
-   **Isolation**: The service runs in its own Docker container but shares the `storage/models` volume with ComfyUI to avoid data duplication.

## Model Loading Strategy
-   **Shared Volume**: Models are looked for in `/app/models/Qwen3-TTS` first. If not found, they are downloaded from HuggingFace/ModelScope.
-   **Flash Attention**: Critical for performance. The Dockerfile installs it from a local wheel if available to speed up build times.

## API Structure
-   `/api/v1/voice-design`: POST endpoint for voice design.
-   `/api/v1/custom-voice`: POST endpoint for custom voice.
-   `/api/v1/voice-clone`: POST endpoint for voice cloning.

-   For production scaling, this synchronous API can be wrapped with a task queue (Celery/Redis) to handle long-running batch jobs asynchronously.

## File Registry & Optimized Batching (New Feature)
To solve the issue of redundant file uploads and sequential processing for Voice Cloning, a **File Registry** was implemented.

### Architecture
-   **Endpoint**: `POST /api/v1/files/upload` accepts a file and returns a unique `file_id`.
-   **Storage**: Files are stored in a temporary directory (`/tmp/tts_files/` in container).
-   **Resolution**: The `VoiceCloneRequest` model was updated to accept `ref_audio` as either a direct path/URL OR a `file_id`. Use `file_id` for optimized batching.

### Batch Flow
1.  **Frontend**: Uploads the file *once* to get `file_id`.
2.  **Frontend**: Groups multiple clone requests (text lines) into a **single API call** using that `file_id`.
3.  **Backend**: Resolves the `file_id` to a local path and processes the batch in parallel on the GPU.
4.  **Output**: Returns download URLs for the generated audio files.

## Batch Generation Architecture (Technical)
How can items in a single batch have different durations?

The system uses a **Dynamic Sequence Masking** approach:
1.  **Padding**: All input text and reference codes in a batch are padded to the length of the longest item in that batch.
2.  **Attention Masking**: The Transformer model uses a masking tensor to ensure that attention is only paid to the actual data, ignoring the padding tokens.
3.  **Individual EOS Detection**: During the generation phase, the model predicts tokens for all items in the batch simultaneously. However, it independently monitors for an `<EOS>` (End Of Speech) token for **each item**.
4.  **Post-Process Slicing**: The engine identifies the exact frame where the `<EOS>` token was emitted for each individual sample and "slices" the generated code sequence at that specific point. 

This results in a batch where the GPU performs a single large operation, but the output is a list of audio files with unique, precise durations matching their respective input texts.
