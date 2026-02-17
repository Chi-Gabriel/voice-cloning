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

                # Find the largest group
                largest_op = max(groups, key=lambda k: len(groups[k]))
                items_to_process = groups.pop(largest_op)
                
                # Push deferred groups back to Redis (front of queue)
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
            max_new_tokens = items[0].get("max_new_tokens", 2048)
            top_p = items[0].get("top_p", 0.80)
            top_k = items[0].get("top_k", 20)
            repetition_penalty = items[0].get("repetition_penalty", 1.05)
            
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
                    temperature=temperature,
                    max_new_tokens=max_new_tokens,
                    top_p=top_p,
                    top_k=top_k,
                    repetition_penalty=repetition_penalty
                )

            elif operation == "custom_voice":
                speakers = [item.get("speaker", "Speaker_001") for item in items]
                instructs = [item.get("instruct") for item in items]
                results = tts_engine.generate_custom_voice(
                    text=texts,
                    speaker=speakers,
                    language=languages,
                    instruct=instructs,
                    temperature=temperature,
                    max_new_tokens=max_new_tokens,
                    top_p=top_p,
                    top_k=top_k,
                    repetition_penalty=repetition_penalty
                )

            elif operation == "voice_clone":
                ref_audios = [item.get("ref_audio") for item in items]
                ref_texts = [item.get("ref_text") for item in items]
                results = tts_engine.generate_voice_clone(
                    text=texts,
                    ref_audio=ref_audios,
                    ref_text=ref_texts,
                    language=languages,
                    temperature=temperature,
                    max_new_tokens=max_new_tokens,
                    top_p=top_p,
                    top_k=top_k,
                    repetition_penalty=repetition_penalty
                )

            elif operation == "voice_clone_enhanced":
                ref_audios = [item.get("ref_audio") for item in items]
                ref_texts = [item.get("ref_text") for item in items]
                results = audio_pipeline.process_voice_clone_enhanced(
                    text=texts,
                    ref_audio=ref_audios,
                    ref_text=ref_texts,
                    language=languages,
                    temperature=temperature,
                    max_new_tokens=max_new_tokens,
                    top_p=top_p,
                    top_k=top_k,
                    repetition_penalty=repetition_penalty
                )
            
            # Save results and update status
            for i, item in enumerate(items):
                item_id = item["item_id"]
                try:
                    audio_content = results[i]
                    filename = f"queue_{operation}_{item_id}.wav"
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
