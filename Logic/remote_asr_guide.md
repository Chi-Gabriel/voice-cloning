# Remote ASR Integration Guide (Batch & Queue)

This document provides instructions for integrating a remote service with the **Qwen-ASR Queue**. This is the recommended approach for transcribing large volumes of audio chunks from a separate server.

## Overview

The ASR process follows a **3-step asynchronous pattern** to maximize GPU throughput and prevent timeout errors:

1.  **Upload**: Send raw audio chunks to get persistent `file_id`s.
2.  **Submit**: Batch those `file_id`s into a single `transcribe` queue request.
3.  **Poll/Retrieve**: Monitor the batch status and download the JSON transcripts.

---

## Step 1: Upload Chunks
For every audio chunk, you must first register it with the file store.

**Endpoint:** `POST /api/v1/files/upload`
**Header:** `X-API-Key: YOUR_API_KEY`

**Request (Multipart Form):**
- `file`: The audio chunk (wav, mp3, flac, etc.)

**Response:**
```json
{
  "file_id": "84c08fb9-5d57-4073-960b-2e6c53faad78"
}
```

---

## Step 2: Submit to Queue
Once you have your `file_id`s, group them into a batch. The GPU worker handles up to **16 items simultaneously** in a single GPU pass.

**Endpoint:** `POST /api/v1/queue/submit`
**Header:** `Content-Type: application/json`

**Payload:**
```json
{
  "label": "My Long Recording Job",
  "items": [
    {
      "operation": "transcribe",
      "ref_audio": "file_id_1",
      "language": "auto",
      "return_timestamps": true,
      "custom_id": "chunk_001",
      "text": "" 
    },
    {
      "operation": "transcribe",
      "ref_audio": "file_id_2",
      "language": "English",
      "custom_id": "chunk_002",
      "text": ""
    }
  ]
}
```
*Note: The `text` field is required by the schema but ignored for ASR operations.*

**Response:**
```json
{
  "batch_id": "c76a92...",
  "total_items": 2,
  "item_ids": ["item_uuid_1", "item_uuid_2"],
  "status": "queued"
}
```

---

## Step 3: Poll for Results
Poll the status of your batch. The GPU worker will process the items in chunks of 16.

**Endpoint:** `GET /api/v1/queue/status/{batch_id}`

**Response (In Progress):**
```json
{
  "status": "processing",
  "completed": 0,
  "total": 2,
  "items": [
    { "item_id": "...", "status": "processing", "url": null },
    { "item_id": "...", "status": "queued", "url": null }
  ]
}
```

**Response (Done):**
```json
{
  "status": "completed",
  "items": [
    {
      "item_id": "...",
      "custom_id": "chunk_001",
      "status": "done",
      "url": "/api/v1/files/queue_transcribe_uuid.json"
    }
  ]
}
```

---

## Step 4: Error Handling
If an item fails (e.g., corrupted audio, OOM error), the status for that specific item will change to `error`.

**Response (With Error):**
```json
{
  "status": "partial", 
  "completed": 1,
  "failed": 1,
  "total": 2,
  "items": [
    {
      "item_id": "item_uuid_1",
      "status": "done",
      "url": "/api/v1/files/..."
    },
    {
      "item_id": "item_uuid_2",
      "status": "error",
      "url": null,
      "error": "Short audio: transcript could not be generated."
    }
  ]
}
```
*   **`status: "partial"`**: Means the batch is still running or finished with some failures.
*   **`status: "error"`**: Means the batch itself failed (rare).
*   **Item Level `error`**: Check the `error` string for specific details (e.g., *"Model timed out"*, *"Invalid audio format"*).

---

## Step 5: Retrieve Transcript
The `url` in the result points to a JSON file (not audio). Fetch it to get the text.

**Endpoint:** `GET /api/v1/files/{file_id_from_url}`

**JSON Content:**
```json
{
  "text": "The transcribed text for this chunk.",
  "language": "English",
  "timestamps": [
    {"start": 0.0, "end": 0.25, "text": "The"},
    {"start": 0.25, "end": 0.8, "text": "transcribed"},
    {"start": 0.8, "end": 1.1, "text": "text"},
    {"start": 1.1, "end": 1.3, "text": "for"},
    {"start": 1.3, "end": 1.4, "text": "this"},
    {"start": 1.4, "end": 1.8, "text": "chunk."}
  ]
}
```
*Note: Timestamps are only present if `return_timestamps: true` was sent in the queue payload or batch request.*

---

## Best Practices for "Many Chunks"

### 1. Batch Size Optimization
Even if you have 1,000 chunks, do not submit 1,000 separate `submit` requests. 
- Submit batches of **100-200 items** per `submit` call.
- The `GPUWorker` will automatically slice these into groups of **16** (your current hardware limit) to feed the GPU, but grouping them in the queue reduces Redis overhead.

### 2. Model Swap Management
The server unloads TTS models to load ASR models.
- If you are doing both Voice Cloning and ASR, try to send all ASR batches together. 
- This prevents the server from constantly "swapping" models in VRAM, which takes ~3-5 seconds per swap.

### 3. File Registry Expiry
Files (both uploaded chunks and resulting JSONs) are stored in `/tmp/tts_files`.
- The current expiry is set to **30 minutes**.
- Ensure your remote service downloads the JSON results within 30 minutes of completion, or they will be auto-deleted.

### 4. Language Hinting
If you know the language of your recording, specify it (e.g., `"language": "English"`). This prevents the model from running an extra Language Identification (LID) pass on every single chunk, slightly improving speed.
