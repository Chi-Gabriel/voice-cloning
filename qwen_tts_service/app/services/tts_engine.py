import torch
import soundfile as sf
import os
import io
import gc
import logging
import tempfile
import shutil
from typing import List, Optional, Union, Tuple
from qwen_tts import Qwen3TTSModel
from app.core.config import settings

logger = logging.getLogger(__name__)

class TTSEngine:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TTSEngine, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        self.device = settings.DEVICE
        self.models = {}
        self.model_configs = {
            "VoiceDesign": "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign",
            "VoiceClone": "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
            "CustomVoice": "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"
        }

    def _get_model(self, model_key: str):
        # Single Active Model Policy:
        # If the requested model is not loaded, unload everything else first.
        if model_key not in self.models:
            self._unload_all_models()
            
            # Check if model type is enabled in config
            enabled_flag = getattr(settings, f"ENABLE_{model_key.upper().replace(' ', '_')}", True)
            if not enabled_flag:
                raise RuntimeError(f"{model_key} is disabled in configuration.")
            
            model_id = self.model_configs.get(model_key)
            if not model_id:
                raise ValueError(f"Unknown model key: {model_key}")
                
            self._load_model(model_key, model_id)
            
        return self.models[model_key]

    def _unload_all_models(self):
        """Unload all models to free VRAM."""
        if not self.models:
            return
            
        logger.info("Unloading existing models to free VRAM...")
        keys = list(self.models.keys())
        for key in keys:
            del self.models[key]
        
        self.models = {}
        gc.collect()
        torch.cuda.empty_cache()
        logger.info("VRAM cleared.")

    def _load_model(self, model_key: str, model_id: str):
        try:
            # Check local path first
            # 1. Check strict model_key mapping (legacy structure)
            local_path = os.path.join(settings.MODEL_ROOT, model_key)
            
            # 2. If not found, check repo-based name (current structure)
            if not os.path.exists(local_path):
                repo_name = model_id.split("/")[-1]
                local_path_repo = os.path.join(settings.MODEL_ROOT, repo_name)
                if os.path.exists(local_path_repo):
                    local_path = local_path_repo
            
            model_source = local_path if os.path.exists(local_path) else model_id
            
            logger.info(f"Loading {model_key} model from {model_source}...")
            # Use torch_dtype correctly to avoid the Flash Attention warning
            self.models[model_key] = Qwen3TTSModel.from_pretrained(
                model_source,
                device_map=self.device,
                torch_dtype=torch.bfloat16,
                attn_implementation="flash_attention_2",
            )
            logger.info(f"{model_key} loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load {model_key}: {e}")
            raise e

    def generate_voice_design(self, text: Union[str, List[str]], instruct: Union[str, List[str]], language: Union[str, List[str]] = "Auto", temperature: float = 1.0, max_new_tokens: int = 2048, top_p: float = 0.80, top_k: int = 20, repetition_penalty: float = 1.05) -> List[bytes]:
        model = self._get_model("VoiceDesign")
        wavs, sr = model.generate_voice_design(
            text=text,
            language=language,
            instruct=instruct,
            temperature=temperature,
            max_new_tokens=max_new_tokens,
            top_p=top_p,
            top_k=top_k,
            repetition_penalty=repetition_penalty,
        )
        return self._process_output(wavs, sr)

    def generate_custom_voice(self, text: Union[str, List[str]], speaker: Union[str, List[str]], language: Union[str, List[str]] = "Auto", instruct: Optional[Union[str, List[str]]] = None, temperature: float = 1.0, max_new_tokens: int = 2048, top_p: float = 0.80, top_k: int = 20, repetition_penalty: float = 1.05) -> List[bytes]:
        model = self._get_model("CustomVoice")
        wavs, sr = model.generate_custom_voice(
            text=text,
            language=language,
            speaker=speaker,
            instruct=instruct,
            temperature=temperature,
            max_new_tokens=max_new_tokens,
            top_p=top_p,
            top_k=top_k,
            repetition_penalty=repetition_penalty,
        )
        return self._process_output(wavs, sr)

    def generate_voice_clone(self, text: Union[str, List[str]], ref_audio: Union[str, List[str], bytes], ref_text: Optional[Union[str, List[str]]] = None, language: Union[str, List[str]] = "Auto", temperature: float = 1.0, max_new_tokens: int = 2048, top_p: float = 0.80, top_k: int = 20, repetition_penalty: float = 1.05) -> List[bytes]:
        model = self._get_model("VoiceClone")
        
        # Handle bytes as ref_audio (write to temp file)
        temp_files = []
        try:
            processed_ref_audio = ref_audio
            if isinstance(ref_audio, bytes):
                fd, path = tempfile.mkstemp(suffix=".wav")
                with os.fdopen(fd, 'wb') as f:
                    f.write(ref_audio)
                processed_ref_audio = path
                temp_files.append(path)
            elif isinstance(ref_audio, list):
                processed_ref_audio = []
                for item in ref_audio:
                    if isinstance(item, bytes):
                        fd, path = tempfile.mkstemp(suffix=".wav")
                        with os.fdopen(fd, 'wb') as f:
                            f.write(item)
                        processed_ref_audio.append(path)
                        temp_files.append(path)
                    else:
                        processed_ref_audio.append(item)

            # Determine x_vector_only_mode based on ref_text
            if isinstance(text, list):
                # Batch mode
                if ref_text is None:
                    x_vector_only_mode = [True] * len(text)
                    ref_text = [""] * len(text)
                elif isinstance(ref_text, list):
                    x_vector_only_mode = [t is None or t == "" for t in ref_text]
                    # Replace None with empty string for the model
                    ref_text = [t if t is not None else "" for t in ref_text]
                else:
                    # Single ref_text for a batch
                    x_vector_only_mode = [False] * len(text)
            else:
                # Single mode
                x_vector_only_mode = ref_text is None or ref_text == ""
                if ref_text is None:
                    ref_text = ""

            # Ensure all batch inputs have matching lengths for the library
            if isinstance(text, list):
                count = len(text)
                if not isinstance(language, list):
                    language = [language] * count
                if not isinstance(processed_ref_audio, list):
                    processed_ref_audio = [processed_ref_audio] * count
                if not isinstance(ref_text, list):
                    ref_text = [ref_text] * count
                if not isinstance(x_vector_only_mode, list):
                    x_vector_only_mode = [x_vector_only_mode] * count

            logger.info(f"Generating voice clone batch of size {len(text) if isinstance(text, list) else 1}")
            
            wavs, sr = model.generate_voice_clone(
                text=text,
                language=language,
                ref_audio=processed_ref_audio,
                ref_text=ref_text,
                x_vector_only_mode=x_vector_only_mode,
                temperature=temperature,
                max_new_tokens=max_new_tokens,
                top_p=top_p,
                top_k=top_k,
                repetition_penalty=repetition_penalty,
            )
            
            outputs = self._process_output(wavs, sr)
            # Debug: check if outputs are identical
            if len(outputs) > 1:
                unique_outputs = len(set(outputs))
                logger.info(f"Batch generation complete. Unique audios: {unique_outputs}/{len(outputs)}")
                if unique_outputs == 1:
                    logger.warning("CRITICAL: All generated audios in batch are identical!")
                    
            return outputs
        finally:
            # Cleanup temp files
            for path in temp_files:
                try:
                    os.remove(path)
                except:
                    pass

    def _process_output(self, wavs: List[any], sr: int) -> List[bytes]:
        """Convert raw waveforms to WAV bytes."""
        audio_bytes_list = []
        for wav in wavs:
            buffer = io.BytesIO()
            sf.write(buffer, wav, sr, format='WAV')
            buffer.seek(0)
            audio_bytes_list.append(buffer.getvalue())
        return audio_bytes_list

tts_engine = TTSEngine()
