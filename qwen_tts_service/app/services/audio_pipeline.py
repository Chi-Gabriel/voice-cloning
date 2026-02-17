import os
import time
import logging
import tempfile
import concurrent.futures
from typing import List, Optional, Union, Dict
from pathlib import Path
from app.core.config import settings
from app.services.resampler import resampler
from app.services.noise_removal import noise_removal
from app.services.tts_engine import tts_engine
from app.services.file_store import file_store
from app.core.config import settings

# --- Pipeline Tuning ---
# Set these to False to bypass specific stages of the enhancement pipeline
RUN_PRE_PROCESSING = False # Controls Stage 1 & 2 (Resample & Noise Removal)
RUN_POST_PROCESSING = True # Controls Stage 4 & 5 (Resample & Noise Removal)
# -----------------------

logger = logging.getLogger(__name__)

class AudioPipeline:
    def __init__(self):
        self.temp_dir = Path("/tmp/tts_files")
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def _pre_process_single_file(self, ref_path: str) -> str:
        """Runs stages 1-2 for a single file: Resample -> Denoise -> Cleaned Path."""
        # Stage 1: Resample
        resampled_path = resampler._resample_single(ref_path)
        
        # Stage 2: Noise Removal
        denoised_path = noise_removal._denoise_single(resampled_path)
        
        # Cleanup intermediate if it's not the original or final
        if resampled_path != ref_path and resampled_path != denoised_path:
            try:
                os.remove(resampled_path)
            except:
                pass
                
        return denoised_path

    def _post_process_single_file(self, wav_bytes: bytes, index: int) -> bytes:
        """Runs stages 4-5 for a single TTS output: Save -> Resample -> Denoise -> Bytes."""
        temp_path = self.temp_dir / f"tts_out_{index}_{os.getpid()}.wav"
        with open(temp_path, "wb") as f:
            f.write(wav_bytes)
            
        # Stage 4: Resample
        resampled_path = resampler._resample_single(str(temp_path))
        
        # Stage 5: Noise Removal
        denoised_path = noise_removal._denoise_single(resampled_path)
        
        # Read final result
        with open(denoised_path, "rb") as f:
            final_bytes = f.read()
            
        # Cleanup all temporary files in the chain
        for path in {str(temp_path), resampled_path, denoised_path}:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except:
                pass
                
        return final_bytes

    def process_voice_clone_enhanced(
        self, 
        text: Union[str, List[str]], 
        ref_audio: Union[str, List[str]], 
        ref_text: Optional[Union[str, List[str]]] = None, 
        language: Union[str, List[str]] = "Auto", 
        temperature: float = 1.0
    ) -> List[bytes]:
        """
        Runs the optimized enhanced voice cloning pipeline:
        [Parallel CPU Pre-processing] -> [Batched GPU TTS] -> [Parallel CPU Post-processing]
        """
        # 1. Resolve ref_audio paths
        ref_paths = self._resolve_paths(ref_audio)
        
        # 2. Pre-processing: Resample & Noise Removal (Parallelized)
        max_workers = settings.RESAMPLE_MAX_WORKERS
        if RUN_PRE_PROCESSING:
            logger.info(f"Pipeline: Parallel pre-processing {len(ref_paths)} reference files")
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                clean_ref_paths = list(executor.map(self._pre_process_single_file, ref_paths))
        else:
            logger.info("Pipeline: Bypassing stages 1-2 (Pre-Processing) as per tuning configuration")
            clean_ref_paths = ref_paths
        
        # 3. Generate TTS (Batched on GPU)
        logger.info("Pipeline: Stage 3 - Generating TTS with cleaned references (Batched)")
        tts_wav_bytes_list = tts_engine.generate_voice_clone(
            text=text,
            ref_audio=clean_ref_paths if isinstance(ref_audio, list) else clean_ref_paths[0],
            ref_text=ref_text,
            language=language,
            temperature=temperature
        )
        
        # 4. Post-processing: Resample & Noise Removal (Parallelized)
        if RUN_POST_PROCESSING:
            logger.info(f"Pipeline: Parallel post-processing {len(tts_wav_bytes_list)} generated outputs")
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                # We use list(executor.map(...)) to maintain order
                final_wav_bytes_list = list(executor.map(
                    self._post_process_single_file, 
                    tts_wav_bytes_list, 
                    range(len(tts_wav_bytes_list))
                ))
        else:
            logger.info("Pipeline: Bypassing stages 4-5 (Post-Processing) as per tuning configuration")
            final_wav_bytes_list = tts_wav_bytes_list
            
        return final_wav_bytes_list

    def _resolve_paths(self, ref_audio: Union[str, List[str], bytes]) -> List[str]:
        """Resolves ref_audio (ID, path, or raw bytes) to absolute filesystem paths."""
        paths = []
        
        # Handle single raw bytes input
        if isinstance(ref_audio, bytes):
            temp_path = self.temp_dir / f"ref_input_{os.getpid()}_{int(time.time())}.wav"
            with open(temp_path, "wb") as f:
                f.write(ref_audio)
            return [str(temp_path)]

        if isinstance(ref_audio, str):
            ref_audio = [ref_audio]
        
        for item in ref_audio:
            # If a list contains bytes (unlikely but possible in some batch scenarios)
            if isinstance(item, bytes):
                temp_path = self.temp_dir / f"ref_input_list_{os.getpid()}_{int(time.time())}.wav"
                with open(temp_path, "wb") as f:
                    f.write(item)
                paths.append(str(temp_path))
                continue

            # Check if it's already an absolute path
            if isinstance(item, str) and os.path.isabs(item) and os.path.exists(item):
                paths.append(item)
                continue

            # Check if it's a file_id in file_store
            path = file_store.get_path(item)
            if path:
                paths.append(str(path))
            else:
                raise ValueError(f"Reference audio not found or invalid: {item}")
        return paths

audio_pipeline = AudioPipeline()
