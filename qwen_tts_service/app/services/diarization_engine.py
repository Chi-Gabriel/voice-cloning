import torch
import logging
import gc
import os
import time
import threading
import torchaudio
from pathlib import Path
from typing import List, Union, Optional, Dict, Any
from pyannote.audio import Pipeline
from app.core.config import settings
from app.models.diarization_models import DiarizationSegment

logger = logging.getLogger(__name__)

class DiarizationEngine:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DiarizationEngine, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        from app.services.model_manager import model_manager
        model_manager.register_engine("diarization", self)
        
        # Use settings device, fallback to CPU
        requested_device = settings.DEVICE
        if torch.cuda.is_available():
            self.device = torch.device(requested_device)
        else:
            logger.warning(f"CUDA requested but not available. Falling back to CPU for diarization.")
            self.device = torch.device("cpu")
            
        self.pipeline = None
        logger.info(f"DiarizationEngine initialized on {self.device}")

    def unload(self):
        # We don't use the lock here to avoid deadlock if acquire is waiting for another engine's unload
        # but ModelManager calls unload under its own lock. ASREngine/TTSEngine don't lock unload.
        if self.pipeline is not None:
            logger.info("Unloading Diarization pipeline to free VRAM...")
            del self.pipeline
            self.pipeline = None
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            logger.info("Diarization Memory cleared.")

    def _ensure_model_loaded(self):
        if self.pipeline is None:
            from app.services.model_manager import model_manager
            # Coordinate with ModelManager to unload other models if needed
            model_manager.acquire("diarization")
            
            if not settings.ENABLE_DIARIZATION:
                raise RuntimeError("Diarization is disabled in configuration.")
            
            if not settings.HF_TOKEN:
                logger.warning("HF_TOKEN not set. Pyannote 3.1 is a gated model and requires a token.")

            repo_id = settings.DIARIZATION_MODEL
            logger.info(f"Loading Diarization pipeline: {repo_id}...")
            t0 = time.perf_counter()
            
            try:
                self.pipeline = Pipeline.from_pretrained(
                    repo_id,
                    use_auth_token=settings.HF_TOKEN
                )
            except Exception as e:
                logger.error(f"Error loading diarization pipeline: {e}")
                raise RuntimeError(f"Failed to load diarization pipeline {repo_id}. Ensure HF_TOKEN is valid and you have accepted the model terms.")
            
            if self.pipeline is None:
                raise RuntimeError(f"Failed to load diarization pipeline {repo_id}. Check HF_TOKEN and model gate access.")
                
            self.pipeline.to(self.device)
            logger.info(f"Diarization pipeline loaded in {time.perf_counter() - t0:.2f}s")

    def diarize(self, 
                audio_paths: Union[str, List[str]], 
                num_speakers: Optional[Union[int, List[Optional[int]]]] = None,
                min_speakers: Optional[Union[int, List[Optional[int]]]] = None,
                max_speakers: Optional[Union[int, List[Optional[int]]]] = None) -> List[Dict[str, Any]]:
        
        with self._lock:
            self._ensure_model_loaded()
            
            if isinstance(audio_paths, str):
                audio_paths = [audio_paths]
                num_speakers = [num_speakers] if num_speakers is not None else [None]
                min_speakers = [min_speakers] if min_speakers is not None else [None]
                max_speakers = [max_speakers] if max_speakers is not None else [None]

            # Ensure lists match length
            if len(num_speakers) < len(audio_paths):
                num_speakers = num_speakers + [None] * (len(audio_paths) - len(num_speakers))
            if len(min_speakers) < len(audio_paths):
                min_speakers = min_speakers + [None] * (len(audio_paths) - len(min_speakers))
            if len(max_speakers) < len(audio_paths):
                max_speakers = max_speakers + [None] * (len(audio_paths) - len(max_speakers))

            all_results = []
            
            for i, path in enumerate(audio_paths):
                if not os.path.exists(path):
                    logger.error(f"Diarization: File not found: {path}")
                    all_results.append({"segments": [], "num_speakers": 0, "error": "File not found"})
                    continue

                t_start = time.perf_counter()
                
                try:
                    # Optimized Loading: Pre-load waveform to avoid pyannote's slow internal I/O
                    waveform, sample_rate = torchaudio.load(path)
                    
                    # Ensure mono
                    if waveform.shape[0] > 1:
                        waveform = waveform.mean(dim=0, keepdim=True)
                    
                    # Move to device
                    waveform = waveform.to(self.device)
                    
                    # Diarization parameters
                    params = {}
                    if num_speakers[i] is not None:
                        params["num_speakers"] = int(num_speakers[i])
                    if min_speakers[i] is not None:
                        params["min_speakers"] = int(min_speakers[i])
                    if max_speakers[i] is not None:
                        params["max_speakers"] = int(max_speakers[i])

                    # Run inference
                    # Passing a dict with waveform and sample_rate is the standard way to optimize I/O in pyannote
                    diarization = self.pipeline({"waveform": waveform, "sample_rate": sample_rate}, **params)
                    
                    segments = []
                    unique_speakers = set()
                    for turn, _, speaker in diarization.itertracks(yield_label=True):
                        segments.append(DiarizationSegment(
                            speaker=speaker,
                            start=turn.start,
                            end=turn.end
                        ))
                        unique_speakers.add(speaker)
                    
                    dur = time.perf_counter() - t_start
                    logger.info(f"Diarized {path} ({len(segments)} segments, {len(unique_speakers)} speakers) in {dur:.2f}s")
                    
                    all_results.append({
                        "segments": segments,
                        "num_speakers": len(unique_speakers)
                    })
                except Exception as e:
                    logger.error(f"Error diarizing {path}: {e}")
                    all_results.append({"segments": [], "num_speakers": 0, "error": str(e)})

            return all_results

diarization_engine = DiarizationEngine()
