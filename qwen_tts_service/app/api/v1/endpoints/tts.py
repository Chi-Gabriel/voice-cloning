from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from typing import List, Union, Optional
from app.models.requests import VoiceDesignRequest, VoiceCloneRequest, CustomVoiceRequest, LanguageEnum, LANGUAGE_MAP
from app.models.responses import TTSResponse, TTSResponseItem
from app.services.tts_engine import tts_engine
import base64
import time

router = APIRouter()

@router.post("/voice-design", response_model=TTSResponse)
async def generate_voice_design(request: VoiceDesignRequest):
    """
    Generate audio from text description (Voice Design).
    Returns base64 encoded WAV audio list.
    """
    try:
        start_time = time.perf_counter()
        # Convert Enum to string for internal engine
        lang = request.language
        if isinstance(lang, list):
            lang = [LANGUAGE_MAP.get(l, "Auto") for l in lang]
        elif isinstance(lang, LanguageEnum):
            lang = LANGUAGE_MAP.get(lang, "Auto")
            
        audio_bytes_list = tts_engine.generate_voice_design(
            text=request.text,
            instruct=request.instruct,
            language=lang
        )
        
        items = []
        for audio in audio_bytes_list:
            items.append(TTSResponseItem(audio_base64=base64.b64encode(audio).decode('utf-8')))
            
        execution_time = time.perf_counter() - start_time
        return TTSResponse(items=items, performance=execution_time)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid Input: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@router.post("/custom-voice", response_model=TTSResponse)
async def generate_custom_voice(request: CustomVoiceRequest):
    """
    Generate audio using a specific speaker (Custom Voice).
    Returns base64 encoded WAV audio list.
    """
    try:
        start_time = time.perf_counter()
        # Convert Enum to string for internal engine
        lang = request.language
        if isinstance(lang, list):
            lang = [LANGUAGE_MAP.get(l, "Auto") for l in lang]
        elif isinstance(lang, LanguageEnum):
            lang = LANGUAGE_MAP.get(lang, "Auto")

        audio_bytes_list = tts_engine.generate_custom_voice(
            text=request.text,
            speaker=request.speaker,
            language=lang,
            instruct=request.instruct
        )
        
        items = []
        for audio in audio_bytes_list:
            items.append(TTSResponseItem(audio_base64=base64.b64encode(audio).decode('utf-8')))
            
        execution_time = time.perf_counter() - start_time
        return TTSResponse(items=items, performance=execution_time)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid Input: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@router.post("/voice-clone-file", response_model=TTSResponse)
async def generate_voice_clone_file(
    text: str = Form(...),
    ref_audio: UploadFile = File(...),
    ref_text: Optional[str] = Form(None),
    language: LanguageEnum = Form(LanguageEnum.AUTO),
    custom_id: Optional[str] = Form(None)
):
    """
    Clone a voice from an uploaded reference audio file.
    Returns base64 encoded WAV audio list.
    """
    try:
        start_time = time.perf_counter()
        content = await ref_audio.read()
        
        # Map language code to full name
        engine_lang = LANGUAGE_MAP.get(language, "Auto")
        
        audio_bytes_list = tts_engine.generate_voice_clone(
            text=text,
            ref_audio=content,
            ref_text=ref_text,
            language=engine_lang
        )
        
        items = []
        # Single item response for file upload endpoint
        for audio in audio_bytes_list:
             items.append(TTSResponseItem(
                 audio_base64=base64.b64encode(audio).decode('utf-8'),
                 custom_id=custom_id
             ))
             
        execution_time = time.perf_counter() - start_time
        return TTSResponse(items=items, performance=execution_time)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid Input: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    finally:
        await ref_audio.close()

@router.post("/voice-clone", response_model=TTSResponse)
async def generate_voice_clone(request: VoiceCloneRequest):
    """
    Clone a voice from reference audio (path or URL).
    Returns base64 encoded WAV audio list with custom IDs if provided.
    """
    try:
        start_time = time.perf_counter()
        # Convert Enum to string for internal engine
        lang = request.language
        if isinstance(lang, list):
            lang = [LANGUAGE_MAP.get(l, "Auto") for l in lang]
        elif isinstance(lang, LanguageEnum):
            lang = LANGUAGE_MAP.get(lang, "Auto")

        audio_bytes_list = tts_engine.generate_voice_clone(
            text=request.text,
            ref_audio=request.ref_audio,
            ref_text=request.ref_text,
            language=lang
        )
        
        # Handle response mapping
        items = []
        
        # Normalize custom_id to a list if it was a single string, or create list of None
        custom_ids = request.custom_id
        if custom_ids is None:
            custom_ids = [None] * len(audio_bytes_list)
        elif isinstance(custom_ids, str):
             # If single string passed but multiple audios generated (batch text with single ID?), 
             # usually likely means single mode, but good to be safe.
             custom_ids = [custom_ids] * len(audio_bytes_list)
        
        # Ensure lengths match just in case
        if len(custom_ids) < len(audio_bytes_list):
            custom_ids.extend([None] * (len(audio_bytes_list) - len(custom_ids)))
            
        for audio, cid in zip(audio_bytes_list, custom_ids):
            items.append(TTSResponseItem(
                audio_base64=base64.b64encode(audio).decode('utf-8'),
                custom_id=cid
            ))
            
        execution_time = time.perf_counter() - start_time
        return TTSResponse(items=items, performance=execution_time)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid Input: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
