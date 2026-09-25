import json
from functools import lru_cache
from typing import Annotated, Any, Literal

from pydantic import BeforeValidator, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_cors(v: Any) -> list[str]:
    if isinstance(v, str):
        if not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        parsed = json.loads(v)
        if isinstance(parsed, list) and all(isinstance(item, str) for item in parsed):
            return parsed
        raise ValueError("CORS origins JSON must be a list of strings")
    elif isinstance(v, list) and all(isinstance(item, str) for item in v):
        return v
    raise ValueError("Invalid format for CORS origins")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Core Application Settings
    PROJECT_NAME: str = "GuardLLM Security Gateway"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False

    # Security & CORS Controls
    ALLOWED_ORIGINS: Annotated[list[str], BeforeValidator(parse_cors)] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # LLM Provider Configuration (Google Gemini)
    GEMINI_API_KEY: str = Field(default="", description="Google Gemini API Key")
    GEMINI_MODEL: str = Field(
        default="gemini-1.5-flash",
        description="Default Google Gemini model name",
    )
    GEMINI_API_BASE_URL: str = Field(
        default="https://generativelanguage.googleapis.com/v1beta",
        description="Base URL for Gemini API",
    )
    LLM_REQUEST_TIMEOUT_SECONDS: float = Field(
        default=30.0,
        description="Timeout in seconds for outbound calls to the LLM provider",
    )

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


@lru_cache
def get_settings() -> Settings:
    """Returns a cached singleton instance of application settings."""
    return Settings()


settings: Settings = get_settings()
