from openai import AsyncOpenAI
from app.config import settings


def get_openai_client() -> AsyncOpenAI:
    """Provides an AsyncOpenAI client configured for Groq or OpenAI."""
    if settings.LLM_PROVIDER == "groq":
        return AsyncOpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
        )
    return AsyncOpenAI(api_key=settings.OPENAI_API_KEY)