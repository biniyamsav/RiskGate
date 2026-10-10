from fastapi import Request, status
from fastapi.responses import JSONResponse


class LLMServiceException(Exception):
    """Raised when an external LLM call fails or returns an invalid payload."""

    def __init__(self, detail: str = "LLM provider evaluation failed."):
        self.detail = detail
        super().__init__(self.detail)


async def llm_service_exception_handler(request: Request, exc: LLMServiceException):
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "error": "Risk Assessment Service Unavailable",
            "detail": exc.detail,
        },
    )