import json
import uuid
import redis
import logging
from typing import List, Optional, Dict, Any, Tuple
from app.core.config import settings
from app.models.queue_models import (
    QueueItemRequest, 
    QueueBatchSubmitRequest, 
    QueueBatchSubmitResponse,
    QueueBatchStatusResponse,
    QueueItemStatus
)

logger = logging.getLogger(__name__)

class QueueService:
    def __init__(self):
        self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
        self.queue_key = "gpu_queue"
        
    def submit_batch(self, request: QueueBatchSubmitRequest) -> QueueBatchSubmitResponse:
        batch_id = str(uuid.uuid4())
        item_ids = []
        
        # Initialize batch metadata in Redis
        batch_data = {
            "batch_id": batch_id,
            "label": request.label or "",
            "total": len(request.items),
            "completed": 0,
            "failed": 0,
            "status": "queued"
        }
        self.redis.hset(f"batch:{batch_id}", mapping=batch_data)
        
        # Pipeline Redis commands for efficiency
        pipe = self.redis.pipeline()
        
        for item in request.items:
            item_id = str(uuid.uuid4())
            item_ids.append(item_id)
            
            # Item payload for the queue
            item_payload = item.model_dump()
            item_payload["item_id"] = item_id
            item_payload["batch_id"] = batch_id
            
            # Store item metadata/status
            item_data = {
                "item_id": item_id,
                "batch_id": batch_id,
                "status": "queued",
                "custom_id": item.custom_id or "",
                "payload": json.dumps(item_payload)
            }
            pipe.hset(f"item:{item_id}", mapping=item_data)
            
            # Track items belonging to this batch
            pipe.rpush(f"batch_items:{batch_id}", item_id)
            
            # Push to GPU queue
            pipe.rpush(self.queue_key, json.dumps(item_payload))
            
        pipe.execute()
        
        return QueueBatchSubmitResponse(
            batch_id=batch_id,
            total_items=len(request.items),
            item_ids=item_ids
        )
        
    def pop_items(self, count: int) -> List[Dict[str, Any]]:
        """Atomic pop of up to 'count' items from the queue."""
        items = []
        try:
            # redis-py lpop with count returns a list if count > 1
            raw_items = self.redis.lpop(self.queue_key, count)
            if raw_items:
                if isinstance(raw_items, str):
                    raw_items = [raw_items]
                
                pipe = self.redis.pipeline()
                for raw in raw_items:
                    item = json.loads(raw)
                    # Update status to processing
                    pipe.hset(f"item:{item['item_id']}", "status", "processing")
                    # Update batch status if it was 'queued'
                    pipe.hset(f"batch:{item['batch_id']}", "status", "processing")
                    items.append(item)
                pipe.execute()
        except Exception as e:
            logger.error(f"Error popping items from Redis: {e}")
            
        return items

    def push_to_front(self, items: List[Dict[str, Any]]):
        """Push items back to the front of the queue (e.g. if deferred)."""
        if not items:
            return
        pipe = self.redis.pipeline()
        for item in reversed(items):
            # Reset status to queued
            pipe.hset(f"item:{item['item_id']}", "status", "queued")
            pipe.lpush(self.queue_key, json.dumps(item))
        pipe.execute()

    def mark_done(self, item_id: str, url: str):
        item_data = self.redis.hgetall(f"item:{item_id}")
        if not item_data:
            return
            
        batch_id = item_data["batch_id"]
        
        pipe = self.redis.pipeline()
        pipe.hset(f"item:{item_id}", "status", "done")
        pipe.hset(f"item:{item_id}", "url", url)
        
        # Atomically increment completed count
        pipe.hincrby(f"batch:{batch_id}", "completed", 1)
        pipe.execute()
        
        self._update_batch_final_status(batch_id)

    def mark_error(self, item_id: str, error: str):
        item_data = self.redis.hgetall(f"item:{item_id}")
        if not item_data:
            return
            
        batch_id = item_data["batch_id"]
        
        pipe = self.redis.pipeline()
        pipe.hset(f"item:{item_id}", "status", "error")
        pipe.hset(f"item:{item_id}", "error", error)
        
        # Atomically increment failed count
        pipe.hincrby(f"batch:{batch_id}", "failed", 1)
        pipe.execute()
        
        self._update_batch_final_status(batch_id)

    def _update_batch_final_status(self, batch_id: str):
        batch = self.redis.hgetall(f"batch:{batch_id}")
        if not batch:
            return
            
        total = int(batch["total"])
        completed = int(batch.get("completed", 0))
        failed = int(batch.get("failed", 0))
        
        if completed + failed >= total:
            final_status = "completed" if failed == 0 else "partial"
            if failed == total:
                final_status = "error"
            self.redis.hset(f"batch:{batch_id}", "status", final_status)

    def get_batch_status(self, batch_id: str) -> Optional[QueueBatchStatusResponse]:
        batch = self.redis.hgetall(f"batch:{batch_id}")
        if not batch:
            return None
            
        item_ids = self.redis.lrange(f"batch_items:{batch_id}", 0, -1)
        items = []
        for item_id in item_ids:
            item_data = self.redis.hgetall(f"item:{item_id}")
            if item_data:
                items.append(QueueItemStatus(
                    item_id=item_id,
                    custom_id=item_data.get("custom_id") or None,
                    status=item_data.get("status", "queued"),
                    url=item_data.get("url") or None,
                    error=item_data.get("error") or None
                ))
        
        return QueueBatchStatusResponse(
            batch_id=batch_id,
            label=batch.get("label") or None,
            status=batch.get("status", "queued"),
            total=int(batch["total"]),
            completed=int(batch.get("completed", 0)),
            failed=int(batch.get("failed", 0)),
            items=items
        )

queue_service = QueueService()
