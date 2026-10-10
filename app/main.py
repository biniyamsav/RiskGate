from fastapi import FastAPI
from app.api.health import router as health_router
from app.api.predictions import router as predictions_router
from app.config import settings
from app.core.exceptions import (
    LLMServiceException,
    llm_service_exception_handler,
)

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

app.add_exception_handler(
    LLMServiceException, llm_service_exception_handler
)


@app.get("/", tags=["Health"])
async def root():
    return {
        "service": settings.APP_NAME,
        "status": "online",
        "docs": "/docs",
    }


app.include_router(health_router)
app.include_router(predictions_router, prefix=settings.API_V1_STR) 