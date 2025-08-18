from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_NAME: str = Field(default="AI Character Backend")
    APP_VERSION: str = Field(default="0.1.0")
    ENVIRONMENT: str = Field(default="development")

    # Server
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)
    RELOAD: bool = Field(default=True)

    # LLM / Vector config (placeholders)
    GROQ_API_KEY: Optional[str] = None
    HF_API_TOKEN: Optional[str] = None
    VECTOR_STORE_PATH: str = Field(default="data/vectorstore")

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache(maxsize=1)
def get_settings() -> "Settings":
    return Settings()
