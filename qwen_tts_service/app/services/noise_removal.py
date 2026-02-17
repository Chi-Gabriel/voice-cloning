import os
import logging
import concurrent.futures
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import soundfile as sf
import torch
from app.core.config import settings

logger = logging.getLogger(__name__)

class NoiseRemovalService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(NoiseRemovalService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        self.model = None
        self.df_state = None
        self.max_workers = settings.NOISE_REMOVAL_MAX_WORKERS
        self.storage_dir = Path("/tmp/tts_files")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.device = torch.device(settings.DEVICE if torch.cuda.is_available() else "cpu")

    def _ensure_model(self):
        """Lazy load the DeepFilterNet model."""
        if self.model is not None:
            return

        logger.info("Initializing DeepFilterNet model...")
        try:
            from df.enhance import init_df
            # init_df returns (model, df_state, nb_frequency_bins)
            self.model, self.df_state, _ = init_df()
            self.model.to(self.device)
            self.model.eval()
            logger.info("DeepFilterNet model initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize DeepFilterNet: {e}")
            raise e

    def remove_noise_files(self, file_paths: List[str]) -> Dict[str, str]:
        """
        Remove noise from a list of files in parallel.
        Returns a map of {old_path: new_path}.
        Old files are deleted.
        """
        results = {}
        if not file_paths:
            return results

        self._ensure_model()
        logger.info(f"Removing noise from {len(file_paths)} files with {self.max_workers} workers")

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_path = {executor.submit(self._denoise_single, path): path for path in file_paths}
            for future in concurrent.futures.as_completed(future_to_path):
                old_path = future_to_path[future]
                try:
                    new_path = future.result()
                    results[old_path] = new_path
                    if old_path != new_path and os.path.exists(old_path):
                        os.remove(old_path)
                except Exception as e:
                    logger.error(f"Failed to denoise {old_path}: {e}")
                    results[old_path] = old_path

        return results

    def _denoise_single(self, path: str) -> str:
        """Worker function for denoising a single file."""
        try:
            from df.enhance import enhance
            import soundfile as sf
            
            # Load audio using soundfile
            audio_np, sr = sf.read(path)
            
            # DeepFilterNet requirement: 48kHz
            if sr != 48000:
                # We expect the input to be 48kHz due to Stage 1 (Resampler)
                # But just in case, we log it.
                logger.warning(f"NoiseRemovalService expected 48kHz, got {sr}Hz for {path}")
            
            # Convert to torch tensor [C, S] then add batch dim [1, C, S]
            if audio_np.ndim == 1:
                audio_torch = torch.from_numpy(audio_np[None, :]).float()
            else:
                audio_torch = torch.from_numpy(audio_np.T).float() # [S, C] -> [C, S]
            
            # DeepFilterNet enhance
            with torch.inference_mode():
                enhanced = enhance(self.model, self.df_state, audio_torch)
                
            # Convert back to numpy [S, C] for soundfile
            # enhanced is [1, C, T] or [C, T]
            enhanced_np = enhanced.detach().cpu().squeeze(0).numpy().T
            
            # Save new file
            p = Path(path)
            new_path = str(p.parent / f"{p.stem}_clean{p.suffix}")
            sf.write(new_path, enhanced_np, 48000)
            
            return new_path
        except Exception as e:
            logger.error(f"Error in _denoise_single for {path}: {e}")
            raise e

noise_removal = NoiseRemovalService()
