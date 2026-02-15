from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.endpoints import tts
from app.core.security import get_api_key

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
    tts.router, 
    prefix=settings.API_V1_STR, 
    tags=["TTS"],
    dependencies=[Depends(get_api_key)]
)

@app.get("/health")
def health_check():
    return {"status": "ok", "version": settings.VERSION}
