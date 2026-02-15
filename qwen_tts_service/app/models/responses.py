from pydantic import BaseModel
from typing import List, Optional

class TTSResponseItem(BaseModel):
    audio_base64: str
    custom_id: Optional[str] = None

class TTSResponse(BaseModel):
    items: List[TTSResponseItem]
    performance: float = 0.0
