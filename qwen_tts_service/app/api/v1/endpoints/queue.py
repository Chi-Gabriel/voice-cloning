from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from app.models.queue_models import (
    QueueBatchSubmitRequest, 
    QueueBatchSubmitResponse, 
    QueueBatchStatusResponse
)
from app.services.queue_service import queue_service
import time

router = APIRouter()

@router.post("/queue/submit", response_model=QueueBatchSubmitResponse)
async def submit_to_queue(request: QueueBatchSubmitRequest):
    """
    Submit a batch of TTS requests to the async processing queue.
    Returns a batch_id and a list of item_ids for tracking.
    """
    if not request.items:
        raise HTTPException(status_code=400, detail="Batch items list cannot be empty")
    
    try:
        response = queue_service.submit_batch(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit to queue: {str(e)}")

@router.get("/queue/status/{batch_id}", response_model=QueueBatchStatusResponse)
async def get_queue_status(batch_id: str):
    """
    Check the status and progress of a previously submitted batch.
    Includes status for each individual item in the batch.
    """
    status = queue_service.get_batch_status(batch_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Batch ID {batch_id} not found")
    return status

@router.get("/queue/results/{batch_id}", response_model=QueueBatchStatusResponse)
async def get_queue_results(batch_id: str):
    """
    Convenience endpoint to get only completed results from a batch.
    """
    status = queue_service.get_batch_status(batch_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Batch ID {batch_id} not found")
    
    # Optional: Filter for only 'done' or 'error' items if needed, 
    # but the current schema already includes all items with their URLs.
    return status
