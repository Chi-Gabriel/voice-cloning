from pydantic import BaseModel, Field
from typing import List, Optional, Union
import time

class DiarizeFileItem(BaseModel):
    file_id: str
    custom_id: Optional[str] = None
    num_speakers: Optional[int] = None
    min_speakers: Optional[int] = None
    max_speakers: Optional[int] = None

class DiarizeBatchRequest(BaseModel):
    files: List[DiarizeFileItem]

class DiarizationSegment(BaseModel):
    speaker: str
    start: float
    end: float

class DiarizeResultItem(BaseModel):
    file_id: str
    custom_id: Optional[str] = None
    segments: List[DiarizationSegment]
    num_speakers: int

class DiarizeBatchResponse(BaseModel):
    items: List[DiarizeResultItem]
    performance: float

class DiarizeSingleResponse(BaseModel):
    segments: List[DiarizationSegment]
    num_speakers: int
    performance: float
