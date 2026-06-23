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
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8080"
    FABRIC_PATTERNS_DIR: str = str(ROOT_DIR / ".agents" / "fabric_patterns")
    API_KEY: str = ""  # Set to require client API key authentication

    @property
    def ai_enabled(self) -> bool:
        """Check if any LLM backend is configured (LM Studio or Gemini)."""
        return bool(self.LM_STUDIO_API_BASE) or bool(self.GEMINI_API_KEY)

    class Config:
        env_file = ".env"

settings = Settings()
