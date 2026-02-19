import torch
import logging
import gc
import os
import threading
from typing import List, Union, Optional
from qwen_asr import Qwen3ASRModel
from app.core.config import settings

logger = logging.getLogger(__name__)

# Constants for ASR Engine
ASR_MODEL_ID = "Qwen/Qwen3-ASR-1.7B"
ASR_DTYPE = torch.bfloat16
ASR_ATTN_IMPL = "flash_attention_2"
ASR_MAX_NEW_TOKENS = 256

class ASREngine:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ASREngine, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        from app.services.model_manager import model_manager
        model_manager.register_engine("asr", self)
        
        # Robust device detection
        requested_device = settings.DEVICE
        has_cuda = torch.cuda.is_available() and torch.cuda.device_count() > 0
        
        if requested_device.startswith("cuda") and not has_cuda:
            logger.warning(f"CUDA requested ({requested_device}) but no GPUs detected. Falling back to CPU.")
            self.device = "cpu"
        else:
            self.device = requested_device
            
        self.model = None

    def unload(self):
        """Unload the ASR model to free VRAM."""
        if self.model is not None:
            logger.info("Unloading ASR model to free VRAM...")
            del self.model
            self.model = None
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            logger.info("ASR Memory cleared.")

    def _ensure_model_loaded(self):
        if self.model is None:
            from app.services.model_manager import model_manager
            model_manager.acquire("asr")
            
            # Check if model type is enabled
            if not settings.ENABLE_ASR:
                raise RuntimeError("ASR is disabled in configuration.")
                
            # Check for local path (mapped from storage/models/Qwen3-ASR)
            repo_name = ASR_MODEL_ID.split("/")[-1]
            model_source = os.path.join(settings.ASR_MODEL_ROOT, repo_name)
            
            if not os.path.exists(model_source):
                logger.info(f"Local ASR model not found at {model_source}, will download from {ASR_MODEL_ID}")
                model_source = ASR_MODEL_ID
            
            logger.info(f"Loading ASR model from {model_source}...")
            self.model = Qwen3ASRModel.from_pretrained(
                model_source,
                dtype=ASR_DTYPE,
                device_map=self.device,
                attn_implementation=ASR_ATTN_IMPL,
                max_inference_batch_size=settings.ASR_MAX_BATCH_SIZE,
                max_new_tokens=ASR_MAX_NEW_TOKENS
            )
            logger.info("ASR model loaded successfully.")

    def transcribe(self, audio: Union[str, List[str]], language: Optional[Union[str, List[str]]] = None, return_timestamps: bool = False) -> List[any]:
        """
        Transcribe audio files using GPU batch inference.
        Returns a list of result objects.
        """
        with self._lock:
            self._ensure_model_loaded()
            
            # Ensure audio is a list for consistent batch processing
            if isinstance(audio, str):
                audio = [audio]
                if language and isinstance(language, str):
                    language = [language]

            logger.info(f"ASR Engine: Transcribing batch of {len(audio)} items")
            results = self.model.transcribe(
                audio=audio,
                language=language,
                return_time_stamps=return_timestamps
            )
            return results

asr_engine = ASREngine()
