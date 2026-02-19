import os
import time
import logging
import tempfile
import concurrent.futures
from typing import List, Optional, Union, Dict
from pathlib import Path
from app.core.config import settings
from app.services.fb_denoiser import fb_denoiser
from app.services.super_res import super_res
from app.services.tts_engine import tts_engine
from app.services.file_store import file_store

# --- Pipeline Tuning ---
# Set these to False to bypass specific stages of the enhancement pipeline
RUN_PRE_PROCESSING = False   # Controls Denoise & 16k Normalization of Ref Audio
RUN_POST_PROCESSING = True  # Controls Denoise & 16k Normalization of TTS Output
RUN_UPSAMPLING = True       # Controls AI Super-Resolution (16k -> 48k)
# -----------------------

logger = logging.getLogger(__name__)

class AudioPipeline:
    def __init__(self):
        self.temp_dir = Path("/tmp/tts_files")
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def _pre_process_single_file(self, ref_path: str) -> str:
        """Runs pre-processing for a single file: Denoise + 16k Normalization."""
        # Use FBDenoiser for both cleaning and 16k normalization
        results = fb_denoiser.process_files([ref_path])
        return results.get(ref_path, ref_path)

    def process_voice_clone_enhanced(
        self, 
        text: Union[str, List[str]], 
        ref_audio: Union[str, List[str]], 
        ref_text: Optional[Union[str, List[str]]] = None, 
        language: Union[str, List[str]] = "Auto", 
        temperature: float = 0.3
    ) -> List[bytes]:
        """
        Runs the optimized enhanced voice cloning pipeline:
        [Parallel CPU Pre-processing] -> [Batched GPU TTS] -> [Batched GPU Post-processing]
        """
        # 1. Resolve ref_audio paths
        ref_paths = self._resolve_paths(ref_audio)
        
        # 2. Pre-processing: Denoise & 16k Normalize (Parallelized)
        max_workers = settings.RESAMPLE_MAX_WORKERS
        if RUN_PRE_PROCESSING:
            logger.info(f"Pipeline: Parallel pre-processing {len(ref_paths)} reference files")
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                clean_ref_paths = list(executor.map(self._pre_process_single_file, ref_paths))
        else:
            logger.info("Pipeline: Bypassing Pre-Processing")
            clean_ref_paths = ref_paths
        
        # 3. Generate TTS (Batched on GPU)
        logger.info(f"Pipeline: Stage 3 - Generating TTS (Batched) for {len(ref_paths)} items")
        t0 = time.perf_counter()
        tts_wav_bytes_list = tts_engine.generate_voice_clone(
            text=text,
            ref_audio=clean_ref_paths if isinstance(ref_audio, list) else clean_ref_paths[0],
            ref_text=ref_text,
            language=language,
            temperature=temperature
        )
        t_tts = time.perf_counter() - t0
        logger.info(f"Pipeline: Stage 3 (TTS) complete in {t_tts:.2f}s")
        
        # 4. & 5. Post-processing: Batched Denoise & 16k Normalize (GPU)
        import io
        import torch
        import soundfile as sf
        
        current_wav_bytes = tts_wav_bytes_list
        current_sr = 16000

        if RUN_POST_PROCESSING:
            logger.info(f"Pipeline: Batched GPU post-denoising {len(current_wav_bytes)} outputs")
            t_post_start = time.perf_counter()
            wav_tensors = []
            for wav_bytes in current_wav_bytes:
                data, current_sr = sf.read(io.BytesIO(wav_bytes))
                wav_tensors.append(torch.from_numpy(data[None, :]).float() if data.ndim == 1 else torch.from_numpy(data.T).float())

            clean_tensors = fb_denoiser.process_batch_tensors(wav_tensors, current_sr)
            t_denoise = time.perf_counter() - t_post_start
            logger.info(f"Pipeline: Stage 4/5 (Denoise) complete in {t_denoise:.2f}s")
            
            current_sr = 16000 # Denoiser normalizes to 16k
            
            # 6. Upsampling (Optional Post-Stage)
            if RUN_UPSAMPLING:
                logger.info(f"Pipeline: Batched GPU upsampling {len(clean_tensors)} outputs to 48kHz")
                t_up_start = time.perf_counter()
                upsampled_tensors = super_res.process_batch_tensors(clean_tensors, current_sr)
                output_tensors = upsampled_tensors
                current_sr = 48000
                t_upsample = time.perf_counter() - t_up_start
                logger.info(f"Pipeline: Stage 6 (Upsample) complete in {t_upsample:.2f}s")
            else:
                output_tensors = clean_tensors

            # Convert back to bytes
            final_wav_bytes_list = []
            for wav in output_tensors:
                buffer = io.BytesIO()
                sf.write(buffer, wav.squeeze(0).numpy(), current_sr, format='WAV')
                final_wav_bytes_list.append(buffer.getvalue())
        else:
            logger.info("Pipeline: Bypassing Post-Processing")
            final_wav_bytes_list = current_wav_bytes
            
        total_time = time.perf_counter() - t0
        logger.info(f"Pipeline: Optimized voice clone enhanced complete in {total_time:.2f}s")
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
                logger.info(f"Pipeline: Resolved file_id '{item}' to {path}")
                paths.append(str(path))
            else:
                # Debug storage dir
                found_files = list(self.temp_dir.glob("*"))
                logger.error(f"Pipeline: Failed to resolve '{item}'. Files in {self.temp_dir}: {len(found_files)}")
                if len(found_files) < 10:
                    logger.error(f"Existing files: {[f.name for f in found_files]}")
                raise ValueError(f"Reference audio not found or invalid: {item}")
        return paths

audio_pipeline = AudioPipeline()
