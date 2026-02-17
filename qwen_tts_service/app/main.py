from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.endpoints import tts, files, pipeline, queue
from app.core.security import get_api_key
from app.services.gpu_worker import gpu_worker

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Router with API Key security
app.include_router(
    files.router,
    prefix=f"{settings.API_V1_STR}/files",
    tags=["Files"]
)

app.include_router(
    pipeline.router,
    prefix=settings.API_V1_STR,
    tags=["Pipeline"],
    dependencies=[Depends(get_api_key)]
)

app.include_router(
    queue.router,
    prefix=settings.API_V1_STR,
    tags=["Queue"],
    dependencies=[Depends(get_api_key)]
)

app.include_router(
    tts.router, 
    prefix=settings.API_V1_STR, 
    tags=["TTS"],
    dependencies=[Depends(get_api_key)]
)

from fastapi.staticfiles import StaticFiles
import os

# Serve UI (Static Files)
# Ensure the directory exists relative to this file
ui_path = os.path.join(os.path.dirname(__file__), "..", "ui")
if os.path.exists(ui_path):
    app.mount("/", StaticFiles(directory=ui_path, html=True), name="ui")

@app.on_event("startup")
async def startup_event():
    gpu_worker.start()

@app.on_event("shutdown")
async def shutdown_event():
    gpu_worker.stop()

@app.get("/health")
def health_check():
    return {"status": "ok", "version": settings.VERSION}
