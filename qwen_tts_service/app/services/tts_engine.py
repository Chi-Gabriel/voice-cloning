import torch
import soundfile as sf
import os
import io
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
        if model_key not in self.models:
            # Check if model type is enabled in config
            enabled_flag = getattr(settings, f"ENABLE_{model_key.upper().replace(' ', '_')}", True)
            if not enabled_flag:
                raise RuntimeError(f"{model_key} is disabled in configuration.")
            
            model_id = self.model_configs.get(model_key)
            if not model_id:
                raise ValueError(f"Unknown model key: {model_key}")
                
            self._load_model(model_key, model_id)
            
        return self.models[model_key]

    def _load_model(self, model_key: str, model_id: str):
        try:
            # Check local path first
            local_path = os.path.join(settings.MODEL_ROOT, model_key)
            model_source = local_path if os.path.exists(local_path) else model_id
            
            logger.info(f"Loading {model_key} model from {model_source}...")
            # We use torch.dtype directly to avoid the warning seen in logs
            self.models[model_key] = Qwen3TTSModel.from_pretrained(
                model_source,
                device_map=self.device,
                dtype=torch.bfloat16,
                attn_implementation="flash_attention_2",
            )
            logger.info(f"{model_key} loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load {model_key}: {e}")
            raise e

    def generate_voice_design(self, text: Union[str, List[str]], instruct: Union[str, List[str]], language: Union[str, List[str]] = "Auto") -> List[bytes]:
        model = self._get_model("VoiceDesign")
        wavs, sr = model.generate_voice_design(
            text=text,
            language=language,
            instruct=instruct,
        )
        return self._process_output(wavs, sr)

    def generate_custom_voice(self, text: Union[str, List[str]], speaker: Union[str, List[str]], language: Union[str, List[str]] = "Auto", instruct: Optional[Union[str, List[str]]] = None) -> List[bytes]:
        model = self._get_model("CustomVoice")
        wavs, sr = model.generate_custom_voice(
            text=text,
            language=language,
            speaker=speaker,
            instruct=instruct,
        )
        return self._process_output(wavs, sr)

    def generate_voice_clone(self, text: Union[str, List[str]], ref_audio: Union[str, List[str], bytes], ref_text: Optional[Union[str, List[str]]] = None, language: Union[str, List[str]] = "Auto") -> List[bytes]:
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

            wavs, sr = model.generate_voice_clone(
                text=text,
                language=language,
                ref_audio=processed_ref_audio,
                ref_text=ref_text,
                x_vector_only_mode=x_vector_only_mode,
            )
            return self._process_output(wavs, sr)
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
