import os
from pathlib import Path
from pydantic_settings import BaseSettings

# Calculate the root path assuming this file is in backend/app/core/config.py
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "Nales-It API"
    MONGODB_URI: str = "mongodb://admin:password@localhost:27017"
    DATABASE_NAME: str = "nales_it"
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    LM_STUDIO_API_BASE: str = "http://127.0.0.1:1234/v1"
    LM_STUDIO_API_KEY: str = "lm-studio"
    LM_STUDIO_MODEL: str = "google/gemma-4-e4b"
    ALLOWED_ORIGINS: str = "*" # Comma-separated list of origins, or *
    FABRIC_PATTERNS_DIR: str = str(ROOT_DIR / ".agents" / "fabric_patterns")

    class Config:
        env_file = ".env"

settings = Settings()
