from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Qwen-TTS API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Model Configuration
    # Using shared volume path by default
    MODEL_ROOT: str = "/app/models/Qwen3-TTS"
    
    # Enable/Disable specific models to save VRAM
    # Default to False for safety, user can enable via ENV
    ENABLE_VOICE_DESIGN: bool = True
    ENABLE_VOICE_CLONE: bool = True
    ENABLE_CUSTOM_VOICE: bool = True
    
    # Device Configuration
    DEVICE: str = "cuda:0"
    
    # Audio Pipeline Configuration
    RESAMPLE_TARGET_SR: int = 48000
    RESAMPLE_MAX_WORKERS: int = 3
    NOISE_REMOVAL_MAX_WORKERS: int = 3
    TTS_MAX_NEW_TOKENS: int = 512 # Caps generation to prevent hallucinations
    
    # Security
    API_KEY: Optional[str] = None
    
    # Async Queue Configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    QUEUE_MAX_BATCH_SIZE: int = 8
    QUEUE_POLL_INTERVAL: float = 0.1

    # ASR Configuration
    # Mapping shared models volume
    ASR_MODEL_ROOT: str = "/app/models/Qwen3-ASR"
    ENABLE_ASR: bool = True
    ASR_MAX_BATCH_SIZE: int = 8 # Safe default for batching

    # Diarization Configuration
    ENABLE_DIARIZATION: bool = True
    DIARIZATION_MODEL: str = "pyannote/speaker-diarization-3.1"
    DIARIZATION_MAX_BATCH_SIZE: int = 4
    HF_TOKEN: Optional[str] = None

    class Config:
        env_file = ".env"

settings = Settings()
