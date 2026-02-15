from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from typing import List, Union, Optional
from app.models.requests import VoiceDesignRequest, VoiceCloneRequest, CustomVoiceRequest, LanguageEnum, LANGUAGE_MAP
from app.models.responses import TTSResponse, TTSResponseItem
from app.services.tts_engine import tts_engine
import base64
import time

router = APIRouter()

from app.services.file_store import file_store

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
            language=lang,
            temperature=request.temperature
        )
        
        items = []
        for audio in audio_bytes_list:
            # Save to file store and get URL
            file_id = file_store.save(audio, "voice_design.wav")
            url = f"/api/v1/files/{file_id}"
            
            items.append(TTSResponseItem(
                audio_base64=base64.b64encode(audio).decode('utf-8'),
                url=url
            ))
            
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
            instruct=request.instruct,
            temperature=request.temperature
        )
        
        items = []
        for audio in audio_bytes_list:
            # Save to file store and get URL
            file_id = file_store.save(audio, "custom_voice.wav")
            url = f"/api/v1/files/{file_id}"
            
            items.append(TTSResponseItem(
                audio_base64=base64.b64encode(audio).decode('utf-8'),
                url=url
            ))
            
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
    custom_id: Optional[str] = Form(None),
    temperature: Optional[float] = Form(0.3) # Added temperature parameter
):
    """
    Clone a voice from an uploaded reference audio file.
    Returns base64 encoded WAV audio list.
    """
    try:
        start_time = time.perf_counter()
        audio_content = await ref_audio.read() # Renamed 'content' to 'audio_content' as per instruction
        
        # Map language code to full name
        engine_lang = LANGUAGE_MAP.get(language, "Auto")
        
        # Pass temperature to engine (defaulting to 0.3 for this endpoint as it uses form fields)
        temp = float(temperature) if temperature is not None else 0.3
        
        audio_bytes_list = tts_engine.generate_voice_clone(
            text=text,
            ref_audio=audio_content, # Changed from 'content' to 'audio_content'
            ref_text=ref_text,
            language=engine_lang, # Kept original 'engine_lang'
            temperature=temp
        )
        
        items = []
        # Single item response for file upload endpoint
        for audio in audio_bytes_list:
             # Save to file store and get URL
             file_id = file_store.save(audio, "voice_clone.wav")
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
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    finally:
        await ref_audio.close()

@router.post("/voice-clone", response_model=TTSResponse)
async def generate_voice_clone(request: VoiceCloneRequest):
    """
    Clone a voice from reference audio (path, URL, or File URI).
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

        # Process ref_audio to resolve file IDs
        processed_ref_audio = request.ref_audio
        
        # Helper to resolve a single ref audio item
        def resolve_ref_audio(item):
            # Check if it looks like a file ID (UUID-ish) but simplistic check for now
            # Or check if it exists in file store
            # For now, let's assume if it is NOT an absolute path starting with /, it might be an ID.
            # actually better: check file_store.get_path(item)
            if isinstance(item, str):
                path = file_store.get_path(item)
                if path:
                    return str(path)
            return item

        if isinstance(processed_ref_audio, list):
            processed_ref_audio = [resolve_ref_audio(item) for item in processed_ref_audio]
        else:
            processed_ref_audio = resolve_ref_audio(processed_ref_audio)

        audio_bytes_list = tts_engine.generate_voice_clone(
            text=request.text,
            ref_audio=processed_ref_audio,
            ref_text=request.ref_text,
            language=lang,
            temperature=request.temperature
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
            # Save to file store and get URL
            file_id = file_store.save(audio, "voice_clone.wav")
            url = f"/api/v1/files/{file_id}"
            print(f"DEBUG: Generated batch item {cid or 'N/A'} -> {url}", flush=True)
            
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
        import traceback
        err_trace = traceback.format_exc()
        print(f"ERROR: {err_trace}", flush=True)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}\n{err_trace}")
