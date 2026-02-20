from fastapi import APIRouter, HTTPException, File, UploadFile, Depends
from typing import List, Optional
import time
import os
import logging
from app.models.diarization_models import (
    DiarizeBatchRequest, DiarizeBatchResponse, DiarizeSingleResponse, 
    DiarizeResultItem, DiarizationSegment
)
from app.services.diarization_engine import diarization_engine
from app.services.file_store import file_store
from app.core.security import get_api_key

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/diarize", response_model=DiarizeBatchResponse, dependencies=[Depends(get_api_key)])
async def diarize_batch(request: DiarizeBatchRequest):
    """
    Diarize multiple audio files in a single batch.
    Accepts a list of file_ids (from /upload) or local paths.
    """
    if not request.files:
        raise HTTPException(status_code=400, detail="Files list cannot be empty")
        
    try:
        start_time = time.perf_counter()
        
        file_paths = []
        file_ids = []
        custom_ids = []
        num_speakers = []
        min_speakers = []
        max_speakers = []
        
        for item in request.files:
            path = file_store.get_path(item.file_id)
            if not path:
                if os.path.exists(item.file_id):
                    path = item.file_id
                else:
                    raise HTTPException(status_code=404, detail=f"File ID or path not found: {item.file_id}")
            
            file_paths.append(str(path))
            file_ids.append(item.file_id)
            custom_ids.append(item.custom_id)
            num_speakers.append(item.num_speakers)
            min_speakers.append(item.min_speakers)
            max_speakers.append(item.max_speakers)
            
        # Diarize
        engine_results = diarization_engine.diarize(
            audio_paths=file_paths,
            num_speakers=num_speakers,
            min_speakers=min_speakers,
            max_speakers=max_speakers
        )
        
        items = []
        for i, res in enumerate(engine_results):
            if "error" in res:
                # Handle error per item
                items.append(DiarizeResultItem(
                    file_id=file_ids[i],
                    custom_id=custom_ids[i],
                    segments=[],
                    num_speakers=0
                ))
                continue
                
            items.append(DiarizeResultItem(
                file_id=file_ids[i],
                custom_id=custom_ids[i],
                segments=res["segments"],
                num_speakers=res["num_speakers"]
            ))
            
        execution_time = time.perf_counter() - start_time
        return DiarizeBatchResponse(items=items, performance=execution_time)
        
    except Exception as e:
        logger.error(f"Diarization batch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/diarize/file", response_model=DiarizeSingleResponse, dependencies=[Depends(get_api_key)])
async def diarize_file(
    audio: UploadFile = File(...),
    num_speakers: Optional[int] = None,
    min_speakers: Optional[int] = None,
    max_speakers: Optional[int] = None
):
    """
    Diarize a single uploaded audio file directly.
    """
    try:
        start_time = time.perf_counter()
        
        # Save to temp file
        content = await audio.read()
        file_id = file_store.save(content, audio.filename)
        path = file_store.get_path(file_id)
        
        # Diarize
        results = diarization_engine.diarize(
            audio_paths=str(path),
            num_speakers=num_speakers,
            min_speakers=min_speakers,
            max_speakers=max_speakers
        )
        
        res = results[0]
        if "error" in res:
            raise HTTPException(status_code=500, detail=res["error"])
            
        execution_time = time.perf_counter() - start_time
        
        return DiarizeSingleResponse(
            segments=res["segments"],
            num_speakers=res["num_speakers"],
            performance=execution_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Diarization file failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await audio.close()
