from pydantic import BaseModel
from typing import List, Optional, Union
from enum import Enum

class ASRLanguageEnum(str, Enum):
    AUTO = "auto"
    ZH = "zh"
    EN = "en"
    CANTONESE = "yue"
    ARABIC = "ar"
    GERMAN = "de"
    FRENCH = "fr"
    SPANISH = "es"
    PORTUGUESE = "pt"
    INDONESIAN = "id"
    ITALIAN = "it"
    KOREAN = "ko"
    RUSSIAN = "ru"
    THAI = "th"
    VIETNAMESE = "vi"
    JAPANESE = "ja"
    TURKISH = "tr"
    HINDI = "hi"
    MALAY = "ms"
    DUTCH = "nl"
    SWEDISH = "sv"
    DANISH = "da"
    FINNISH = "fi"
    POLISH = "pl"
    CZECH = "cs"
    FILIPINO = "tl"
    PERSIAN = "fa"
    GREEK = "el"
    HUNGARIAN = "hu"
    MACEDONIAN = "mk"
    ROMANIAN = "ro"

class ASRFileItem(BaseModel):
    file_id: str
    custom_id: Optional[str] = None

class ASRBatchRequest(BaseModel):
    files: List[ASRFileItem]
    language: ASRLanguageEnum = ASRLanguageEnum.AUTO
    return_timestamps: bool = False

class ASRTimestamp(BaseModel):
    start_time: float
    end_time: float
    text: str

class ASRTranscriptItem(BaseModel):
    custom_id: Optional[str] = None
    text: str
    language: str
    timestamps: Optional[List[ASRTimestamp]] = None
    file_id: Optional[str] = None

class ASRBatchResponse(BaseModel):
    items: List[ASRTranscriptItem]
    performance: float

class ASRSingleResponse(BaseModel):
    text: str
    language: str
    timestamps: Optional[List[ASRTimestamp]] = None
    performance: float
