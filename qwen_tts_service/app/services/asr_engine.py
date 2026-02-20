import torch
import logging
import gc
import os
import time
import threading
import soundfile as sf
from pathlib import Path
from typing import List, Union, Optional
from qwen_asr import Qwen3ASRModel
from app.core.config import settings

logger = logging.getLogger(__name__)

# --- ASR Tuning ---
ASR_MODEL_ID = "Qwen/Qwen3-ASR-1.7B"
ASR_ALIGNER_ID = "Qwen/Qwen3-ForcedAligner-0.6B"
ASR_DTYPE = torch.bfloat16
ASR_ATTN_IMPL = "flash_attention_2"
ASR_MAX_NEW_TOKENS = 256
DENOISE_ASR_INPUT = True
# -------------------

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
        
        requested_device = settings.DEVICE
        has_cuda = torch.cuda.is_available() and torch.cuda.device_count() > 0
        
        if requested_device.startswith("cuda") and not has_cuda:
            logger.warning(f"CUDA requested ({requested_device}) but no GPUs detected. Falling back to CPU.")
            self.device = "cpu"
        else:
            self.device = requested_device
            
        self.model = None
        self._temp_dir = Path("/tmp/asr_denoised")
        self._temp_dir.mkdir(parents=True, exist_ok=True)

    def unload(self):
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
            
            if not settings.ENABLE_ASR:
                raise RuntimeError("ASR is disabled in configuration.")
                
            # Determine model and aligner sources
            repo_name = ASR_MODEL_ID.split("/")[-1]
            model_source = os.path.join(settings.ASR_MODEL_ROOT, repo_name)
            if not os.path.exists(model_source):
                logger.info(f"Local ASR model not found at {model_source}, will download from {ASR_MODEL_ID}")
                model_source = ASR_MODEL_ID

            aligner_repo = ASR_ALIGNER_ID.split("/")[-1]
            aligner_source = os.path.join(settings.ASR_MODEL_ROOT, aligner_repo)
            if not os.path.exists(aligner_source):
                aligner_source = ASR_ALIGNER_ID

            logger.info(f"Loading ASR model from {model_source} with aligner {aligner_source}...")
            self.model = Qwen3ASRModel.from_pretrained(
                model_source,
                dtype=ASR_DTYPE,
                device_map=self.device,
                attn_implementation=ASR_ATTN_IMPL,
                max_inference_batch_size=settings.ASR_MAX_BATCH_SIZE,
                max_new_tokens=ASR_MAX_NEW_TOKENS,
                forced_aligner=aligner_source
            )
            logger.info("ASR model loaded successfully.")

    def _denoise_inputs(self, audio_paths: List[str]) -> List[str]:
        from app.services.fb_denoiser import fb_denoiser

        t0 = time.perf_counter()
        logger.info(f"ASR Pre-processing: Denoising {len(audio_paths)} inputs on GPU")

        wav_tensors = []
        sample_rates = []
        for path in audio_paths:
            data, sr = sf.read(path)
            tensor = torch.from_numpy(data[None, :]).float() if data.ndim == 1 else torch.from_numpy(data.T).float().mean(dim=0, keepdim=True)
            wav_tensors.append(tensor)
            sample_rates.append(sr)

        clean_tensors = fb_denoiser.process_batch_tensors(wav_tensors, sample_rates[0])

        clean_paths = []
        for i, tensor in enumerate(clean_tensors):
            out_path = str(self._temp_dir / f"asr_clean_{os.getpid()}_{int(time.time())}_{i}.wav")
            sf.write(out_path, tensor.squeeze(0).numpy(), 16000)
            clean_paths.append(out_path)

        logger.info(f"ASR Pre-processing: Denoised {len(audio_paths)} files in {time.perf_counter() - t0:.2f}s")
        return clean_paths

    def transcribe(self, audio: Union[str, List[str]], language: Optional[Union[str, List[str]]] = None, return_timestamps: bool = False) -> List[any]:
        with self._lock:
            self._ensure_model_loaded()
            
            if isinstance(audio, str):
                audio = [audio]
                if language and isinstance(language, str):
                    language = [language]

            if DENOISE_ASR_INPUT:
                audio = self._denoise_inputs(audio)

            logger.info(f"ASR Engine: Transcribing batch of {len(audio)} items")
            results = self.model.transcribe(
                audio=audio,
                language=language,
                return_time_stamps=return_timestamps
            )

            if DENOISE_ASR_INPUT:
                for p in audio:
                    try:
                        os.remove(p)
                    except OSError:
                        pass

            return results

asr_engine = ASREngine()
