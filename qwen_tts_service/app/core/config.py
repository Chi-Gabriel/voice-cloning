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
    # Security
    API_KEY: Optional[str] = None
    
    class Config:
        env_file = ".env"

settings = Settings()
