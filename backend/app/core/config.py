from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Nales-It API"
    MONGODB_URI: str = "mongodb://admin:password@localhost:27017"
    DATABASE_NAME: str = "nales_it"
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    ALLOWED_ORIGINS: str = "*" # Comma-separated list of origins, or *

    class Config:
        env_file = ".env"

settings = Settings()
