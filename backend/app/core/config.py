"""Central config via Pydantic Settings. No secrets in code."""
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
_ENV_FILE = _BACKEND_DIR / ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE) if _ENV_FILE.exists() else ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Medical LLM (Mistral-7B fine-tuned via OpenAI-compatible server)
    LLM_BASE_URL: str = Field(
        default="http://localhost:11434/v1",
        description="OpenAI-compatible base URL (Ollama, vLLM, or hosted inference)",
    )
    LLM_API_KEY: str = Field(
        default="ollama",
        description="API key for hosted inference; use any value for local Ollama",
    )
    LLM_MODEL: str = Field(
        default="mistral-7b-medical",
        description="Model name/tag served by your inference endpoint",
    )
    LLM_TEMPERATURE: float = Field(default=0.2, description="Sampling temperature")
    LLM_MAX_TOKENS: int = Field(default=1024, description="Max tokens per completion")

    # Optional web search
    TAVILY_API_KEY: str = Field(default="", description="Tavily API key for web search")

    # Services
    QDRANT_URL: str = Field(default="http://localhost:6333", description="Qdrant server URL")

    # Feature flags
    USE_MOCK_MODELS: bool = Field(default=True, description="Use mock vision predictions")

    # Logging
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO", description="Log level"
    )

    # Embedding device: auto (use GPU if available), cpu, cuda
    EMBED_DEVICE: Literal["auto", "cpu", "cuda"] = Field(
        default="auto", description="Device for embedding model"
    )

    # Auth
    JWT_SECRET: str = Field(default="change-me-in-production", description="Secret for JWT")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    JWT_EXPIRE_MINUTES: int = Field(default=60 * 24 * 7, description="Access token expiry (minutes)")

    # Database (SQLite by default)
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./medical_assistant.db",
        description="Async database URL",
    )


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()


settings = get_settings()
