from pydantic import BaseModel
from typing import List, Optional, Union
from enum import Enum

class ASRLanguageEnum(str, Enum):
    AUTO = "auto"
    ZH = "Chinese"
    EN = "English"
    CANTONESE = "Cantonese"
    ARABIC = "Arabic"
    GERMAN = "German"
    FRENCH = "French"
    SPANISH = "Spanish"
    PORTUGUESE = "Portuguese"
    INDONESIAN = "Indonesian"
    ITALIAN = "Italian"
    KOREAN = "Korean"
    RUSSIAN = "Russian"
    THAI = "Thai"
    VIETNAMESE = "Vietnamese"
    JAPANESE = "Japanese"
    TURKISH = "Turkish"
    HINDI = "Hindi"
    MALAY = "Malay"
    DUTCH = "Dutch"
    SWEDISH = "Swedish"
    DANISH = "Danish"
    FINNISH = "Finnish"
    POLISH = "Polish"
    CZECH = "Czech"
    FILIPINO = "Filipino"
    PERSIAN = "Persian"
    GREEK = "Greek"
    HUNGARIAN = "Hungarian"
    MACEDONIAN = "Macedonian"
    ROMANIAN = "Romanian"

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
