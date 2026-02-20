import time
import logging
import threading
import traceback
from typing import List, Dict, Any
from app.core.config import settings
from app.models.requests import LANGUAGE_MAP
from app.services.queue_service import queue_service
from app.services.tts_engine import tts_engine
from app.services.audio_pipeline import audio_pipeline
from app.services.file_store import file_store
from app.services.asr_engine import asr_engine
import json
import os

logger = logging.getLogger(__name__)

class GPUWorker:
    def __init__(self):
        self._stop_event = threading.Event()
        self._thread = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, name="GPUWorkerThread", daemon=True)
        self._thread.start()
        logger.info("GPU Worker Thread started.")

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("GPU Worker Thread stopped.")

    def _run_loop(self):
        logger.info(f"GPU Worker Loop active (Max Batch: {settings.QUEUE_MAX_BATCH_SIZE})")
        while not self._stop_event.is_set():
            try:
                # 1. Fetch items from queue
                batch_items = queue_service.pop_items(settings.QUEUE_MAX_BATCH_SIZE)
                
                if not batch_items:
                    # Sleep if nothing to do
                    time.sleep(settings.QUEUE_POLL_INTERVAL)
                    continue

                # 2. Group items by operation type
                groups = {}
                for item in batch_items:
                    op = item["operation"]
                    if op not in groups:
                        groups[op] = []
                    groups[op].append(item)

                # Prioritize operation that matches the currently active engine to avoid swapping
                from app.services.model_manager import model_manager
                active = model_manager.active_engine
                
                tts_ops = {"voice_design", "custom_voice", "voice_clone", "voice_clone_enhanced"}
                asr_ops = {"transcribe"}
                
                preferred_op = None
                if active == "tts":
                    # Pick largest TTS group available
                    candidate_ops = [op for op in groups if op in tts_ops]
                    if candidate_ops:
                        preferred_op = max(candidate_ops, key=lambda k: len(groups[k]))
                elif active == "asr":
                    # Pick largest ASR group (currently only transcribe)
                    candidate_ops = [op for op in groups if op in asr_ops]
                    if candidate_ops:
                        preferred_op = max(candidate_ops, key=lambda k: len(groups[k]))

                # 3. Find the best group to process
                largest_op = preferred_op or max(groups, key=lambda k: len(groups[k]))
                items_to_process = groups.pop(largest_op)
                
                # Push deferred groups back to Redis (front of queue)
                if groups:
                    logger.info(f"GPU Worker: Deferring {sum(len(v) for v in groups.values())} mixed-type items to avoid model swap")
                    for op, deferred_items in groups.items():
                        queue_service.push_to_front(deferred_items)

                # 3. Process the largest group
                logger.info(f"GPU Worker: Processing {len(items_to_process)} items for operation '{largest_op}'")
                self._process_group(largest_op, items_to_process)

            except Exception as e:
                logger.error(f"Error in GPU Worker Loop: {e}")
                logger.error(traceback.format_exc())
                time.sleep(1) # Back off on error

    def _process_group(self, operation: str, items: List[Dict[str, Any]]):
        try:
            # Common parameters
            texts = [item["text"] for item in items]
            temperature = items[0].get("temperature", 1.0)
            
            # Map the language code (e.g. "en") to model supported string (e.g. "English")
            languages = []
            for item in items:
                lang_code = item.get("language", "auto")
                lang = LANGUAGE_MAP.get(lang_code, "Auto")
                languages.append(lang)
            
            results = []

            if operation == "voice_design":
                instructs = [item.get("instruct", "Happy") for item in items]
                results = tts_engine.generate_voice_design(
                    text=texts,
                    instruct=instructs,
                    language=languages,
                    temperature=temperature
                )

            elif operation == "custom_voice":
                speakers = [item.get("speaker", "Speaker_001") for item in items]
                instructs = [item.get("instruct") for item in items]
                results = tts_engine.generate_custom_voice(
                    text=texts,
                    speaker=speakers,
                    language=languages,
                    instruct=instructs,
                    temperature=temperature
                )

            elif operation == "voice_clone":
                ref_audios = [item.get("ref_audio") for item in items]
                ref_texts = [item.get("ref_text") for item in items]
                results = tts_engine.generate_voice_clone(
                    text=texts,
                    ref_audio=ref_audios,
                    ref_text=ref_texts,
                    language=languages,
                    temperature=temperature
                )

            elif operation == "voice_clone_enhanced":
                valid_items = []
                resolved_refs = []
                for item in items:
                    ref = item.get("ref_audio")
                    # Try to resolve or check absolute path
                    resolved = None
                    if isinstance(ref, str):
                        if os.path.isabs(ref) and os.path.exists(ref):
                            resolved = ref
                        else:
                            resolved = file_store.get_path(ref)
                    
                    if resolved:
                        valid_items.append(item)
                        resolved_refs.append(str(resolved))
                    else:
                        logger.error(f"GPU Worker: Missing reference audio for item {item['item_id']}: {ref}")
                        queue_service.mark_error(item["item_id"], f"Reference audio not found: {ref}")

                if not valid_items:
                    return
                
                # Update items and texts for the valid subset
                items = valid_items
                texts = [item.get("text") for item in items]
                ref_texts = [item.get("ref_text") for item in items]
                languages = [LANGUAGE_MAP.get(item.get("language", "Auto"), "Auto") for item in items]

                results = audio_pipeline.process_voice_clone_enhanced(
                    text=texts,
                    ref_audio=resolved_refs,
                    ref_text=ref_texts,
                    language=languages,
                    temperature=temperature
                )
            elif operation == "transcribe":
                ref_audios = []
                for item in items:
                    path = item.get("ref_audio")
                    # Try to resolve file_id
                    resolved = file_store.get_path(path)
                    ref_audios.append(str(resolved) if resolved else path)
                
                # Use asr language mapping
                from app.api.v1.endpoints.asr import ASR_LANGUAGE_MAP
                from app.models.asr_models import ASRLanguageEnum

                mapped_languages = []
                for item in items:
                    lang_code = item.get("language", "auto")
                    lang_name = None
                    if lang_code != "auto":
                        try:
                            # Try mapping from ISO code
                            enum_val = ASRLanguageEnum(lang_code)
                            lang_name = ASR_LANGUAGE_MAP.get(enum_val)
                        except ValueError:
                            # Fallback: check if it's already a full name like "English"
                            lang_name = lang_code
                    mapped_languages.append(lang_name)
                
                # ASR engine handles list of languages if needed, but here we pass the resolved names
                asr_results = asr_engine.transcribe(
                    audio=ref_audios,
                    language=mapped_languages if any(mapped_languages) else None,
                    return_timestamps=items[0].get("return_timestamps", False)
                )
                
                # Convert results to a serializable format for storage
                results = []
                for res in asr_results:
                    out = {"text": res.text, "language": res.language}
                    if hasattr(res, 'time_stamps') and res.time_stamps:
                        out["timestamps"] = [
                            {"start": ts.start_time, "end": ts.end_time, "text": ts.text}
                            for ts in res.time_stamps
                        ]
                    results.append(json.dumps(out).encode('utf-8'))
            elif operation == "diarize":
                from app.services.diarization_engine import diarization_engine
                
                ref_audios = []
                for item in items:
                    path = item.get("ref_audio")
                    resolved = file_store.get_path(path)
                    ref_audios.append(str(resolved) if resolved else path)
                
                num_speakers = [item.get("num_speakers") for item in items]
                min_speakers = [item.get("min_speakers") for item in items]
                max_speakers = [item.get("max_speakers") for item in items]
                
                diarize_results = diarization_engine.diarize(
                    audio_paths=ref_audios,
                    num_speakers=num_speakers,
                    min_speakers=min_speakers,
                    max_speakers=max_speakers
                )
                
                results = []
                for res in diarize_results:
                    # Convert Pydantic models to dict for JSON serialization
                    segments = [s.model_dump() for s in res["segments"]]
                    out = {
                        "segments": segments,
                        "num_speakers": res["num_speakers"]
                    }
                    if "error" in res:
                        out["error"] = res["error"]
                    results.append(json.dumps(out).encode('utf-8'))
            
            # Save results and update status
            for i, item in enumerate(items):
                item_id = item["item_id"]
                try:
                    audio_content = results[i]
                    ext = ".json" if operation in ["transcribe", "diarize"] else ".wav"
                    filename = f"queue_{operation}_{item_id}{ext}"
                    file_id = file_store.save(audio_content, filename)
                    url = f"/api/v1/files/{file_id}"
                    queue_service.mark_done(item_id, url)
                except Exception as e:
                    logger.error(f"Error saving item {item_id}: {e}")
                    queue_service.mark_error(item_id, str(e))

        except Exception as e:
            logger.error(f"Group processing failed for {operation}: {e}")
            logger.error(traceback.format_exc())
            for item in items:
                queue_service.mark_error(item["item_id"], str(e))

gpu_worker = GPUWorker()
