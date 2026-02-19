import torch
import os
import numpy as np
import logging
import threading
import concurrent.futures
from pathlib import Path
from typing import List, Dict, Optional, Union
import soundfile as sf
from denoiser import pretrained
from app.core.config import settings

# --- Denoiser Tuning ---
DEFAULT_MODEL = "dns48"
MAX_WORKERS = settings.NOISE_REMOVAL_MAX_WORKERS
# -----------------------

logger = logging.getLogger(__name__)

class FBDenoiserService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FBDenoiserService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        self.model = None
        self.device = torch.device(settings.DEVICE if torch.cuda.is_available() else "cpu")
        self.storage_dir = Path("/tmp/tts_files")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def _ensure_model(self):
        """Lazy load the DNS48 model."""
        if self.model is not None:
            return

        with self._lock:
            if self.model is not None:
                return

            logger.info(f"Initializing Facebook Denoiser ({DEFAULT_MODEL}) on {self.device}...")
            try:
                # DNS48 is high quality, wideband (supports up to 48k, internal handling at 16k/48k)
                self.model = pretrained.dns48().to(self.device)
                self.model.eval()
                logger.info("Facebook Denoiser initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize Facebook Denoiser: {e}")
                raise e

    def process_files(self, file_paths: List[str]) -> Dict[str, str]:
        """
        Process a list of files in parallel (Pre-processing stage).
        Ensures 16kHz output regardless of input.
        """
        results = {}
        if not file_paths:
            return results

        self._ensure_model()
        logger.info(f"Denoising {len(file_paths)} files with {MAX_WORKERS} workers")

        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_path = {executor.submit(self._denoise_single_file, path): path for path in file_paths}
            for future in concurrent.futures.as_completed(future_to_path):
                old_path = future_to_path[future]
                try:
                    new_path = future.result()
                    results[old_path] = new_path
                    if old_path != new_path and os.path.exists(old_path):
                        os.remove(old_path)
                except Exception as e:
                    logger.error(f"Failed to process {old_path}: {e}")
                    results[old_path] = old_path

        return results

    def _denoise_single_file(self, path: str) -> str:
        """Worker for single file denoising + 16k normalization."""
        try:
            data, sr = sf.read(path)
            # Load into tensor [1, T]
            if data.ndim == 1:
                wav = torch.from_numpy(data[None, :]).float().to(self.device)
            else:
                wav = torch.from_numpy(data.T).float().to(self.device).mean(dim=0, keepdim=True)
            
            # Denoise
            with torch.no_grad():
                denoised = self.model(wav[None])[0] # [1, T]
            
            # Save as 16kHz (model.sample_rate is 16000 for dns48)
            p = Path(path)
            new_path = str(p.parent / f"{p.stem}_clean_16k.wav")
            denoised_np = denoised.squeeze(0).cpu().numpy()
            sf.write(new_path, denoised_np, 16000)
            
            return new_path
        except Exception as e:
            logger.error(f"Error in _denoise_single_file for {path}: {e}")
            raise e

    def process_batch_tensors(self, wav_tensors: List[torch.Tensor], sr: int) -> List[torch.Tensor]:
        """
        Batched GPU inference for post-processing.
        Expects a list of [1, T] tensors at 'sr' sampling rate.
        Returns a list of [1, T] clean tensors at 16kHz.
        """
        self._ensure_model()
        
        # 1. Gather & Normalize to 16k
        processed_tensors = []
        for wav in wav_tensors:
            wav = wav.to(self.device)
            if sr != 16000:
                import torchaudio.transforms as T
                wav = T.Resample(sr, 16000).to(self.device)(wav)
            processed_tensors.append(wav)
            
        # 2. Batch Inference
        # Note: denoiser model usually prefers single-batch or properly padded batch.
        # For simplicity and robustness against varying lengths, we do a loop 
        # but keep it all on GPU to avoid I/O.
        final_tensors = []
        with torch.no_grad():
            for wav in processed_tensors:
                # Add batch dim [1, 1, T] -> [1, T] result
                clean = self.model(wav[None])[0]
                final_tensors.append(clean.cpu())
                
        return final_tensors

fb_denoiser = FBDenoiserService()
