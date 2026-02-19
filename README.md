# ComfyUI Qwen3 TTS & ASR Voice Clone Setup

This is a production-ready setup for running **Qwen3-TTS** and **Qwen3-ASR** using **ComfyUI** in a Docker container.

## Key Features

- **Enhanced 16kHz Pipeline**: Direct 16kHz denoising and normalization using Facebook's DNS48, bypassing legacy 48kHz resampling stages for maximum fidelity and lower latency.
- **Pre-configured Environment**: Includes Python 3.11, CUDA 12, PyTorch 2.5, and all dependencies.
- **Voice Cloning Ready**: Full support for voice cloning using **Qwen3-TTS-1.7B-CustomVoice**.
- **Accurate Transcription**: Integrated **Qwen3-ASR-1.7B** for converting audio to text.
- **Optimized for Speed**: Uses manual **Flash Attention 2** installation for significantly faster generation.
- **Resilient**: Dependencies are auto-checked and reinstalled on container restarts.
- **Persistent Storage**: All custom nodes, models, and outputs are saved to your local `storage/` directory.

## Prerequisites

- **NVIDIA GPU** (RTX A4000 or similar recommended) with proper drivers.
- **Docker** and **Docker Compose**.
- Internet access for initial download of models (~10GB).

## Installation

1.  **Clone this repository**:
    ```bash
    git clone <your-repo-url>
    cd voice-clone
    ```

2.  **Run the Setup & Start Script**:
    ```bash
    chmod +x start.sh setup.sh
    ./start.sh
    ```
    This script will:
    - Download the specific "Flash Attention" wheel required for optimization.
    - Create necessary storage folders.
    - Launch the Docker container.
    - Automatically download the required Qwen models (TTS and ASR) on first run.

3.  **Wait for Initialization**:
    On first run, it may take a few minutes to download the large model weights. Watch the logs (which appear automatically). Once you see `[INFO] Starting ComfyUI...`, you are ready.

## Usage

1.  Open your browser and navigate to:
    **http://<your-server-ip>:8188/** (or `http://localhost:8188` if running locally).

2.  **Load a Workflow**:
    Drag and drop one of the JSON files from `storage/custom_nodes/ComfyUI-Qwen3-TTS/example_workflows/` onto the dashboard.
    - **Recommended**: `simple_voice_clone-REQUIRES-ASR.json` for voice cloning.

3.  **Start Generating**:
    - Upload a reference audio file (WAV/MP3).
    - Enter the text you want to generate.
    - Click **Queue Prompt**.

## Qwen-TTS API Service

We also provide a standalone, high-performance API for integrating Qwen-TTS into your own applications.

### Starting the API

You can run the API alongside ComfyUI or independently:

```bash
# Run EVERYTHING (ComfyUI + API)
docker compose up -d

# Run ONLY the API
docker compose up -d qwen-api
```

The API will be available at **http://localhost:8000**.
- **Swagger Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### API Features
- **Shared Models**: Uses the same `storage/models` directory as ComfyUI, so you don't need to download models twice.
- **Batch Processing**: Supports batch generation for high throughput.
- **ASR Support**: Built-in endpoints for high-performance audio transcription using Qwen3-ASR.
- **VRAM Coordination**: Intelligent model swapping between TTS and ASR to fit on a single 16GB GPU.

### Key ASR Endpoints
- `POST /api/v1/transcribe`: Efficient batch transcription using `file_id`s.
- `POST /api/v1/transcribe/file`: Single-file direct upload transcription.
- **Async Queue**: Integrated with the batch queue (`operation: "transcribe"`) for large-scale processing.

## Updating Dependencies

If you need to add more Python packages, you can edit `scripts/pre-start.sh`. This script runs every time the container starts and ensures your environment is consistent.

## Troubleshooting

- **Container not starting?**
    Check logs: `docker compose logs -f comfyui-production`
- **Models missing?**
    The system auto-downloads models to `storage/models`. Ensure you have enough disk space (~20GB).
- **Restarting**:
    Simply specific `docker compose restart`. The self-healing script will fix any broken links or missing dependencies.

## Project Structure

- `docker-compose.yaml`: Docker configuration (ComfyUI + Qwen API).
- `qwen_tts_service/`: Source code for the FastAPI backend.
- `start.sh`: Main entry point to run the project.
- `setup.sh`: Helper to download binary dependencies.
- `scripts/pre-start.sh`: The "brain" of the setup - installs/links everything inside the container.
- `storage/`: Persistent data folder (ignored by git).

