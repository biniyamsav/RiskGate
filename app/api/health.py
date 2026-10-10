from fastapi import APIRouter
from app.config import settings

router = APIRouter()


@router.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "app_name": settings.APP_NAME,
        "provider": settings.LLM_PROVIDER,
        "model": settings.LLM_MODEL,
    }