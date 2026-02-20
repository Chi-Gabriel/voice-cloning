from pydantic import BaseModel, Field
from typing import List, Optional, Union, Literal
from .requests import LanguageEnum

class QueueItemRequest(BaseModel):
    text: str
    operation: Literal["voice_design", "voice_clone", "voice_clone_enhanced", "custom_voice", "transcribe", "diarize"]
    # Operation-specific fields
    ref_audio: Optional[str] = None       # file_id or path
    ref_text: Optional[str] = None
    instruct: Optional[Union[str, List[str]]] = None
    speaker: Optional[str] = None
    language: LanguageEnum = LanguageEnum.AUTO
    temperature: float = 1.0
    num_speakers: Optional[int] = None
    min_speakers: Optional[int] = None
    max_speakers: Optional[int] = None
    custom_id: Optional[str] = None       # user-defined tracking ID
    custom_id: Optional[str] = None       # user-defined tracking ID

class QueueBatchSubmitRequest(BaseModel):
    items: List[QueueItemRequest]
    label: Optional[str] = None

class QueueBatchSubmitResponse(BaseModel):
    batch_id: str
    total_items: int
    item_ids: List[str]
    status: str = "queued"

class QueueItemStatus(BaseModel):
    item_id: str
    custom_id: Optional[str] = None
    status: Literal["queued", "processing", "done", "error"]
    url: Optional[str] = None
    error: Optional[str] = None

class QueueBatchStatusResponse(BaseModel):
    batch_id: str
    label: Optional[str] = None
    status: Literal["queued", "processing", "partial", "completed", "error"]
    total: int
    completed: int
    failed: int
    items: List[QueueItemStatus]
