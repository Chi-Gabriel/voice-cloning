from fastapi import APIRouter, HTTPException, Form, File, UploadFile
from app.models.requests import VoiceCloneEnhancedRequest, LanguageEnum, LANGUAGE_MAP
from app.models.responses import TTSResponse, TTSResponseItem
from app.services.audio_pipeline import audio_pipeline
from app.services.file_store import file_store
import base64
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/voice-clone-enhanced", response_model=TTSResponse)
async def generate_voice_clone_enhanced(request: VoiceCloneEnhancedRequest):
    """
    Clone a voice from reference audio (path or file_id) with enhancement.
    Used by the batch processor or pre-uploaded files.
    """
    try:
        start_time = time.perf_counter()
        lang = request.language
        if isinstance(lang, list):
            lang = [LANGUAGE_MAP.get(l, "Auto") for l in lang]
        elif isinstance(lang, LanguageEnum):
            lang = LANGUAGE_MAP.get(lang, "Auto")

        # Resolve file ID if provided
        processed_ref_audio = request.ref_audio
        if isinstance(processed_ref_audio, str):
            path = file_store.get_path(processed_ref_audio)
            if path:
                processed_ref_audio = str(path)

        audio_bytes_list = audio_pipeline.process_voice_clone_enhanced(
            text=request.text,
            ref_audio=processed_ref_audio,
            ref_text=request.ref_text,
            language=lang,
            temperature=request.temperature
        )
        
        items = []
        custom_ids = request.custom_id
        if custom_ids is None:
            custom_ids = [None] * len(audio_bytes_list)
        elif isinstance(custom_ids, str):
            custom_ids = [custom_ids] * len(audio_bytes_list)
        
        if len(custom_ids) < len(audio_bytes_list):
            custom_ids.extend([None] * (len(audio_bytes_list) - len(custom_ids)))
            
        for audio, cid in zip(audio_bytes_list, custom_ids):
            file_id = file_store.save(audio, "voice_clone_enhanced.wav")
            url = f"/api/v1/files/{file_id}"
            
            items.append(TTSResponseItem(
                audio_base64=base64.b64encode(audio).decode('utf-8'),
                url=url,
                custom_id=cid
            ))
            
        execution_time = time.perf_counter() - start_time
        return TTSResponse(items=items, performance=execution_time)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid Input: {str(e)}")
    except Exception as e:
        logger.error(f"Pipeline Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@router.post("/voice-clone-enhanced-file", response_model=TTSResponse)
async def generate_voice_clone_enhanced_file(
    text: str = Form(...),
    ref_audio: UploadFile = File(...),
    ref_text: Optional[str] = Form(None),
    language: LanguageEnum = Form(LanguageEnum.AUTO),
    custom_id: Optional[str] = Form(None),
    temperature: Optional[float] = Form(0.3)
):
    """
    Clone a voice from an uploaded file with enhanced pre/post-processing.
    """
    try:
        start_time = time.perf_counter()
        audio_content = await ref_audio.read()
        
        # Convert Enum to string for internal engine
        lang = LANGUAGE_MAP.get(language, "Auto")
        temp = float(temperature) if temperature is not None else 0.3

        audio_bytes_list = audio_pipeline.process_voice_clone_enhanced(
            text=text,
            ref_audio=audio_content,
            ref_text=ref_text,
            language=lang,
            temperature=temp
        )
        
        items = []
        for audio in audio_bytes_list:
            file_id = file_store.save(audio, "voice_clone_enhanced.wav")
            url = f"/api/v1/files/{file_id}"
            
            items.append(TTSResponseItem(
                audio_base64=base64.b64encode(audio).decode('utf-8'),
                url=url,
                custom_id=custom_id
            ))
            
        execution_time = time.perf_counter() - start_time
        return TTSResponse(items=items, performance=execution_time)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid Input: {str(e)}")
    except Exception as e:
        logger.error(f"Pipeline Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    finally:
        await ref_audio.close()
