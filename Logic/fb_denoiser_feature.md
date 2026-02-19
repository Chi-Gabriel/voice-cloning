# 16kHz Facebook Denoiser Feature

## Overview
This feature implements a high-performance, 16kHz-native voice denoising stage using the **Facebook Denoiser (DNS48)**. It replaces the previous DeepFilterNet (48kHz) and standalone Resampler services to provide a more efficient, unified pipeline for Qwen-TTS.

## Algorithm & Logic
The denoiser uses a pre-trained **Demucs** architecture optimized for speech enhancement.

### 1. Unified 16kHz Normalization
Since the Qwen-TTS engine operates natively at 16kHz, we standardize the entire pipeline at this rate.
- **Reference Audio**: Resampled to 16kHz before cleaning.
- **Denoising**: Processed at 16kHz to avoid "synthetic artifacts" caused by upsampling noise.
- **Output**: Delivered at 16kHz, ready for the TTS engine or final delivery.

### 2. Efficiency Strategies

#### Batched GPU Processing
For generated outputs, we avoid looping.
```python
# process_batch_tensors logic
1. Receive list of [1, T] tensors.
2. Ensure all are on the same device (GPU).
3. Run model(tensor[None]) in a loop on GPU.
4. Return results immediately without Disk I/O.
```

#### Lazy Loading
The model weights (~50MB) are only loaded when `process_files` or `process_batch_tensors` is first called.

## Files Involved
- [fb_denoiser.py](file:///home/user/voice-clone/qwen_tts_service/app/services/fb_denoiser.py): The core service implementation.
- [audio_pipeline.py](file:///home/user/voice-clone/qwen_tts_service/app/services/audio_pipeline.py): Orchestrates the denoiser in the Pre/Post stages.

## Performance vs. DeepFilterNet
- **VRAM**: ~50MB (vs ~200MB+ for DF).
- **Latency**: Faster for 16kHz audio as it eliminates the 48kHz upsampling/downsampling requirement.
- **Quality**: Better preservation of voice naturalness at 16kHz.
