# Performance Optimizations

## Overview
To improve batch processing throughput and system visibility, several optimizations have been implemented across the engine, pipeline, and worker layers.

## Feature 1: Generation Timeouts (`max_new_tokens`)
**Goal**: Prevent "infinite hallucination" loops where the TTS model continues generating noise or repeating tokens indefinitely.
- **Implementation**: The `TTS_MAX_NEW_TOKENS` setting (configured in `config.py`) is passed to all generation methods in `TTSEngine`.
- **Logic**: It caps the autoregressive decoder at a fixed number of codec tokens (e.g., 512 tokens ≈ ~42 seconds).
- **Files**: `app/services/tts_engine.py`, `app/core/config.py`.

## Feature 2: Per-Stage Timing Instrumentation
**Goal**: Provide clear visibility into where time is spent during complex multi-stage batches.
- **Implementation**: `AudioPipeline` now wraps each major stage (TTS, Denoise, Upsample) with `time.perf_counter()`.
- **Metrics**: 
  - TTS Generation time.
  - Batched GPU Denoising time.
  - Batched GPU Upsampling time.
  - Total end-to-end processing time.
- **Output**: Logs are visible in the service output (e.g., `Pipeline: Stage 3 (TTS) complete in 45.2s`).
- **Files**: `app/services/audio_pipeline.py`.

## Feature 3: Smart Batching (Model-Swap Reduction)
**Goal**: Reduce idle "dead time" caused by unloading and reloading 1.7B parameter models (TTS <-> ASR).
- **Problem**: Changing from TTS to ASR takes several seconds of VRAM management and I/O.
- **Solution**: The `GPUWorker` grouping logic is "sticky". When choosing a batch to process, it checks which model is currently active via `ModelManager` and prioritizes tasks of that type even if they aren't the largest group.
## Feature 4: GPU Inference Locking
**Goal**: Prevent model state corruption (`RuntimeError`) and OOM crashes caused by concurrent inference requests.
- **Problem**: The TTS and ASR models are singletons. If the `GPUWorker` (batch 16) and a Web API request (batch 1) hit the model at the same time, they collide on the same KV cache and VRAM allocation.
- **Solution**: Implemented `threading.Lock` in `TTSEngine` and `ASREngine`. 
- **Behavior**: Parallel requests are now queued at the application level. One batch must finish before the next one starts on the GPU.
- **Files**: `app/services/tts_engine.py`, `app/services/asr_engine.py`.
