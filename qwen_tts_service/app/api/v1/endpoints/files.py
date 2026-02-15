from app.core.security import get_api_key
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
from app.services.file_store import file_store
import os

router = APIRouter()

@router.post("/upload", dependencies=[Depends(get_api_key)])
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a file to the temporary registry.
    Returns: { "file_id": "uuid" }
    """
    try:
        content = await file.read()
        file_id = file_store.save(content, file.filename)
        return {"file_id": file_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{file_id}")
async def get_file(file_id: str):
    """
    Download a file by its ID.
    """
    file_path = file_store.get_path(file_id)
    if not file_path or not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found or expired")
        
    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type="audio/wav"  # Defaulting, or could guess
    )
