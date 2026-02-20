# Audio Transcription (ASR) Implementation

This feature integrates Automatic Speech Recognition (ASR) into the Qwen-TTS Studio using the Qwen3-ASR model.

## Files Involved
- [index.html](file:///home/user/voice-clone/qwen_tts_service/ui/index.html): Defines the ASR tab structure and the native preview player.
- [ui.js](file:///home/user/voice-clone/qwen_tts_service/ui/js/ui.js): High-level UI controller for file handling and queue integration.
- [api.js](file:///home/user/voice-clone/qwen_tts_service/ui/js/api.js): Backend API wrapper for ASR endpoints.
- [style.css](file:///home/user/voice-clone/qwen_tts_service/ui/css/style.css): Custom styles for the ASR file list and components.

## UI Logic & Algorithm
1. **File Selection**: Users can drag-and-drop or choose multiple audio files.
2. **Preview Integration**: 
   - Upon selection, the first file is automatically loaded into a native `<audio id="asr-preview">` player.
   - The file list displays all selected files. Clicking a filename in the list (`UI.selectASRPreview`) dynamically updates the `src` of the native player and highlights the active file using the `.is-processing` class.
3. **Transcription Flow**:
   - **Immediate**: Files are uploaded to `/files/upload`, and then a batch request is sent to `/transcribe`. Results are displayed in a formatted text area.
   - **Batch**: Files are uploaded and added to the global `UI.batchQueue` with the `operation: 'transcribe'` parameter. The result in history is provided as a JSON transcript link.

## Design Decisions
- **Native Player**: Replaced custom WaveSurfer-based preview with a native browser `<audio>` element for maximum compatibility and consistency with the Voice Clone tab, as per user feedback.
- **Batching**: Synchronized ASR tasks with the existing TTS batch queue to allow users to process both types of tasks in a single run.

## Input Denoising
Controlled by the `DENOISE_ASR_INPUT` toggle at the top of [asr_engine.py](file:///home/user/voice-clone/qwen_tts_service/app/services/asr_engine.py).

When enabled, audio files are cleaned and normalized to 16kHz using the GPU-batched [fb_denoiser](file:///home/user/voice-clone/qwen_tts_service/app/services/fb_denoiser.py) (`process_batch_tensors`) **before** being passed to the Qwen3-ASR model. Denoised temp files are deleted after transcription completes.

Set `DENOISE_ASR_INPUT = False` to bypass this stage entirely.
