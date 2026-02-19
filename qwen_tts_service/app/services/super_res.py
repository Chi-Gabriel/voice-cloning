import torch
import numpy as np
import logging
import threading
import io
from typing import List, Optional
import soundfile as sf
from NovaSR import FastSR
from app.core.config import settings

# --- SuperRes Tuning ---
TARGET_SR = 48000
# -----------------------

logger = logging.getLogger(__name__)

class SuperResService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SuperResService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        self.upsampler = None
        self.device = torch.device(settings.DEVICE if torch.cuda.is_available() else "cpu")
        self._lock = threading.Lock()

    def _ensure_model(self):
        """Lazy load the NoVaSR model."""
        if self.upsampler is not None:
            return

        with self._lock:
            if self.upsampler is not None:
                return

            logger.info(f"Initializing NoVaSR Upsampler on {self.device}...")
            try:
                self.upsampler = FastSR()
                # Ensure model is on the correct device and float32
                self.upsampler.model.to(self.device).float()
                self.upsampler.model.eval()
                logger.info("NoVaSR Upsampler initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize NoVaSR Upsampler: {e}")
                raise e

    def process_batch_tensors(self, wav_tensors: List[torch.Tensor], sr: int) -> List[torch.Tensor]:
        """
        Batched GPU inference for super-resolution.
        Expects a list of [1, T] tensors at 'sr' sampling rate (ideally 16kHz).
        Returns a list of [1, T] high-res tensors at 48kHz.
        """
        self._ensure_model()
        
        final_tensors = []
        with torch.no_grad():
            for wav in wav_tensors:
                # Ensure correct device and type
                wav = wav.to(self.device).float()
                
                # NoVaSR expects [B, C, T] for F.interpolate(mode='linear')
                # we add the extra dim [1, T] -> [1, 1, T]
                highres = self.upsampler.infer(wav[None]) # returns [1, T_new]
                final_tensors.append(highres.cpu())
                
        return final_tensors

super_res = SuperResService()
