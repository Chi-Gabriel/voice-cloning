from fastapi import APIRouter, HTTPException, File, UploadFile, Depends
from typing import List, Optional
import time
import os
from app.models.asr_models import (
    ASRBatchRequest, ASRBatchResponse, ASRSingleResponse, 
    ASRTranscriptItem, ASRTimestamp, ASRLanguageEnum
)
from app.services.asr_engine import asr_engine
from app.services.file_store import file_store
from app.core.security import get_api_key

router = APIRouter()

ASR_LANGUAGE_MAP = {
    ASRLanguageEnum.ZH: "Chinese",
    ASRLanguageEnum.EN: "English",
    ASRLanguageEnum.CANTONESE: "Cantonese",
    ASRLanguageEnum.ARABIC: "Arabic",
    ASRLanguageEnum.GERMAN: "German",
    ASRLanguageEnum.FRENCH: "French",
    ASRLanguageEnum.SPANISH: "Spanish",
    ASRLanguageEnum.PORTUGUESE: "Portuguese",
    ASRLanguageEnum.INDONESIAN: "Indonesian",
    ASRLanguageEnum.ITALIAN: "Italian",
    ASRLanguageEnum.KOREAN: "Korean",
    ASRLanguageEnum.RUSSIAN: "Russian",
    ASRLanguageEnum.THAI: "Thai",
    ASRLanguageEnum.VIETNAMESE: "Vietnamese",
    ASRLanguageEnum.JAPANESE: "Japanese",
    ASRLanguageEnum.TURKISH: "Turkish",
    ASRLanguageEnum.HINDI: "Hindi",
    ASRLanguageEnum.MALAY: "Malay",
    ASRLanguageEnum.DUTCH: "Dutch",
    ASRLanguageEnum.SWEDISH: "Swedish",
    ASRLanguageEnum.DANISH: "Danish",
    ASRLanguageEnum.FINNISH: "Finnish",
    ASRLanguageEnum.POLISH: "Polish",
    ASRLanguageEnum.CZECH: "Czech",
    ASRLanguageEnum.FILIPINO: "Filipino",
    ASRLanguageEnum.PERSIAN: "Persian",
    ASRLanguageEnum.GREEK: "Greek",
    ASRLanguageEnum.HUNGARIAN: "Hungarian",
    ASRLanguageEnum.MACEDONIAN: "Macedonian",
    ASRLanguageEnum.ROMANIAN: "Romanian"
}

def _map_results(results, custom_ids=None, file_ids=None) -> List[ASRTranscriptItem]:
    items = []
    for i, res in enumerate(results):
        timestamps = None
        if hasattr(res, 'time_stamps') and res.time_stamps:
            timestamps = [
                ASRTimestamp(start_time=ts.start_time, end_time=ts.end_time, text=ts.text)
                for ts in res.time_stamps
            ]
        
        items.append(ASRTranscriptItem(
            custom_id=custom_ids[i] if custom_ids else None,
            text=res.text,
            language=res.language or "",
            timestamps=timestamps,
            file_id=file_ids[i] if file_ids else None
        ))
    return items

@router.post("/transcribe", response_model=ASRBatchResponse, dependencies=[Depends(get_api_key)])
async def transcribe_batch(request: ASRBatchRequest):
    """
    Transcribe multiple audio files in a single GPU batch for maximum efficiency.
    Accepts a list of file_ids (from /upload) or local paths.
    """
    if not request.files:
        raise HTTPException(status_code=400, detail="Files list cannot be empty")
        
    try:
        start_time = time.perf_counter()
        
        # Resolve file IDs to paths
        file_paths = []
        file_ids = []
        custom_ids = []
        
        for item in request.files:
            path = file_store.get_path(item.file_id)
            if not path:
                # If not a file_id, check if it's a valid local path (for internal use)
                if os.path.exists(item.file_id):
                    path = item.file_id
                else:
                    raise HTTPException(status_code=404, detail=f"File ID or path not found: {item.file_id}")
            
            file_paths.append(str(path))
            file_ids.append(item.file_id)
            custom_ids.append(item.custom_id)
            
        # Transcribe
        lang = ASR_LANGUAGE_MAP.get(request.language) if request.language != ASRLanguageEnum.AUTO else None
        results = asr_engine.transcribe(
            audio=file_paths,
            language=lang,
            return_timestamps=request.return_timestamps
        )
        
        items = _map_results(results, custom_ids, file_ids)
        execution_time = time.perf_counter() - start_time
        
        return ASRBatchResponse(items=items, performance=execution_time)
        
    except Exception as e:
        import traceback
        logger_err = traceback.format_exc()
        print(logger_err)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/transcribe/file", response_model=ASRSingleResponse, dependencies=[Depends(get_api_key)])
async def transcribe_file(
    audio: UploadFile = File(...),
    language: ASRLanguageEnum = ASRLanguageEnum.AUTO,
    return_timestamps: bool = False
):
    """
    Transcribe a single uploaded audio file directly.
    """
    try:
        start_time = time.perf_counter()
        
        # Save to temp file
        content = await audio.read()
        file_id = file_store.save(content, audio.filename)
        path = file_store.get_path(file_id)
        
        # Transcribe
        lang = ASR_LANGUAGE_MAP.get(language) if language != ASRLanguageEnum.AUTO else None
        results = asr_engine.transcribe(
            audio=str(path),
            language=lang,
            return_timestamps=return_timestamps
        )
        
        # Since it's a single file, results[0]
        res = results[0]
        timestamps = None
        if hasattr(res, 'time_stamps') and res.time_stamps:
            timestamps = [
                ASRTimestamp(start_time=ts.start_time, end_time=ts.end_time, text=ts.text)
                for ts in res.time_stamps
            ]
            
        execution_time = time.perf_counter() - start_time
        
        return ASRSingleResponse(
            text=res.text,
            language=res.language or "",
            timestamps=timestamps,
            performance=execution_time
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await audio.close()
