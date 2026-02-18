FROM pytorch/pytorch:2.5.1-cuda12.1-cudnn9-runtime

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1


WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    libsndfile1 \
    ffmpeg \
    sox \
    libsox-fmt-all \
    libhdf5-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY qwen_tts_service/requirements.txt .
RUN pip install --no-cache-dir transformers==4.57.3 && \
    pip install --no-cache-dir qwen-tts && \
    pip install --no-cache-dir qwen-asr --no-deps && \
    pip install --no-cache-dir -r requirements.txt

# Install Flash Attention if available locally, otherwise download
COPY scripts/flash_attn-*.whl /tmp/
RUN if [ -f /tmp/flash_attn-*.whl ]; then \
        pip install /tmp/flash_attn-*.whl; \
    else \
        pip install flash-attn --no-build-isolation; \
    fi

# Copy application code
COPY qwen_tts_service/ .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
