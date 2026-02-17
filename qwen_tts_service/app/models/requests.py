from pydantic import BaseModel
from typing import List, Optional, Union

from enum import Enum

class LanguageEnum(str, Enum):
    AUTO = "auto"
    EN = "en"
    ZH = "zh"
    JA = "ja"
    KO = "ko"
    FR = "fr"
    DE = "de"
    ES = "es"
    RU = "ru"
    PT = "pt"
    IT = "it"
    NL = "nl"

# Internal mapping for Qwen-TTS engine
LANGUAGE_MAP = {
    LanguageEnum.AUTO: "Auto",
    LanguageEnum.EN: "English",
    LanguageEnum.ZH: "Chinese",
    LanguageEnum.JA: "Japanese",
    LanguageEnum.KO: "Korean",
    LanguageEnum.FR: "French",
    LanguageEnum.DE: "German",
    LanguageEnum.ES: "Spanish",
    LanguageEnum.RU: "Russian",
    LanguageEnum.PT: "Portuguese",
    LanguageEnum.IT: "Italian",
    LanguageEnum.NL: "Dutch"
}

class VoiceDesignRequest(BaseModel):
    text: Union[str, List[str]]
    instruct: Union[str, List[str]]
    language: Union[LanguageEnum, List[LanguageEnum]] = LanguageEnum.AUTO
    temperature: float = 1.0
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": ["Hello world", "This is a batch request"],
                "instruct": ["Happy", "Sad"],
                "language": ["en", "en"],
                "temperature": 1.0
            }
        }

class CustomVoiceRequest(BaseModel):
    text: Union[str, List[str]]
    speaker: Union[str, List[str]]
    language: Union[LanguageEnum, List[LanguageEnum]] = LanguageEnum.AUTO
    instruct: Optional[Union[str, List[str]]] = None
    temperature: float = 1.0

    class Config:
        json_schema_extra = {
            "example": {
                "text": ["Hello from speaker A", "Hello from speaker B"],
                "speaker": ["Speaker_001", "Speaker_002"],
                "language": "en",
                "instruct": "Neutral",
                "temperature": 1.0
            }
        }

class VoiceCloneRequest(BaseModel):
    text: Union[str, List[str]]
    ref_audio: Union[str, List[str]]
    ref_text: Optional[Union[str, List[str]]] = None
    language: Union[LanguageEnum, List[LanguageEnum]] = LanguageEnum.AUTO
    custom_id: Optional[Union[str, List[str]]] = None
    temperature: float = 1.0

    class Config:
        json_schema_extra = {
            "example": {
                "text": ["First sentence.", "Second sentence."],
                "ref_audio": ["/path/to/audio1.wav", "/path/to/audio2.wav"],
                "ref_text": ["Reference text 1", None],
                "language": "en",
                "custom_id": ["id_123", "id_456"],
                "temperature": 1.0
            }
        }

class VoiceCloneEnhancedRequest(VoiceCloneRequest):
    class Config:
        json_schema_extra = {
            "example": {
                "text": ["First sentence.", "Second sentence."],
                "ref_audio": ["/path/to/audio1.wav", "/path/to/audio2.wav"],
                "ref_text": ["Reference text 1", None],
                "language": "en",
                "custom_id": ["id_123", "id_456"],
                "temperature": 1.0
            }
        }
