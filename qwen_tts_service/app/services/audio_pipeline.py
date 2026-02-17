import os
import time
import logging
import tempfile
from typing import List, Optional, Union, Dict
from pathlib import Path
from app.services.resampler import resampler
from app.services.noise_removal import noise_removal
from app.services.tts_engine import tts_engine
from app.services.file_store import file_store

logger = logging.getLogger(__name__)

class AudioPipeline:
    def __init__(self):
        self.temp_dir = Path("/tmp/tts_files")
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def process_voice_clone_enhanced(
        self, 
        text: Union[str, List[str]], 
        ref_audio: Union[str, List[str]], 
        ref_text: Optional[Union[str, List[str]]] = None, 
        language: Union[str, List[str]] = "Auto", 
        temperature: float = 0.3
    ) -> List[bytes]:
        """
        Runs the enhanced voice cloning pipeline:
        ref_audio -> Resample -> Noise Removal -> TTS -> Resample -> Noise Removal -> Output
        """
        # 1. Resolve ref_audio paths
        ref_paths = self._resolve_paths(ref_audio)
        
        # 2. Pre-processing: Resample ref audio
        logger.info("Pipeline: Stage 1 - Resampling reference audio")
        resample_map = resampler.resample_files(ref_paths)
        denoise_input_paths = list(resample_map.values())
        
        # 3. Pre-processing: Noise Removal on ref audio
        logger.info("Pipeline: Stage 2 - Removing noise from reference audio")
        denoise_map = noise_removal.remove_noise_files(denoise_input_paths)
        clean_ref_paths = list(denoise_map.values())
        
        # 4. Generate TTS
        logger.info("Pipeline: Stage 3 - Generating TTS with cleaned reference")
        # If input was a list, pass list. If it was single, pass single (resolved by tts_engine anyway)
        # However, we need to pass the paths to the engine.
        tts_wav_bytes_list = tts_engine.generate_voice_clone(
            text=text,
            ref_audio=clean_ref_paths if isinstance(ref_audio, list) else clean_ref_paths[0],
            ref_text=ref_text,
            language=language,
            temperature=temperature
        )
        
        # 5. Post-processing: Save TTS outputs to temp files for further processing
        tts_output_paths = []
        for i, wav_bytes in enumerate(tts_wav_bytes_list):
            temp_path = self.temp_dir / f"tts_out_{i}_{os.getpid()}.wav"
            with open(temp_path, "wb") as f:
                f.write(wav_bytes)
            tts_output_paths.append(str(temp_path))
            
        # 6. Post-processing: Resample TTS output
        logger.info("Pipeline: Stage 4 - Resampling generated audio")
        resample_map_post = resampler.resample_files(tts_output_paths)
        denoise_input_paths_post = list(resample_map_post.values())
        
        # 7. Post-processing: Noise Removal on TTS output
        logger.info("Pipeline: Stage 5 - Removing noise from generated audio")
        denoise_map_post = noise_removal.remove_noise_files(denoise_input_paths_post)
        final_output_paths = list(denoise_map_post.values())
        
        # 8. Read final outputs as bytes and cleanup
        logger.info("Pipeline: Final Stage - Reading results and cleanup")
        final_wav_bytes_list = []
        for path in final_output_paths:
            with open(path, "rb") as f:
                final_wav_bytes_list.append(f.read())
            
            # Final cleanup of the processed files
            try:
                os.remove(path)
            except:
                pass
                
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

            # Check if it's a file_id in file_store
            path = file_store.get_path(item)
            if path:
                paths.append(str(path))
            elif isinstance(item, str) and os.path.isabs(item) and os.path.exists(item):
                paths.append(item)
            else:
                raise ValueError(f"Reference audio not found or invalid: {item}")
        return paths

audio_pipeline = AudioPipeline()
