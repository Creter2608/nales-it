from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api.router import api_router
from app.core.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.db.mongodb import connect_to_mongo, close_mongo_connection
    await connect_to_mongo()
    yield
    await close_mongo_connection()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI Quiz Generator Backend",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS origins
allowed_origins = [origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",")]

cors_kwargs = {
    "allow_methods": ["*"],
    "allow_headers": ["*"],
}

if "*" in allowed_origins:
    cors_kwargs["allow_origins"] = ["*"]
    cors_kwargs["allow_credentials"] = False
else:
    cors_kwargs["allow_origins"] = allowed_origins
    cors_kwargs["allow_credentials"] = True

app.add_middleware(
    CORSMiddleware,
    **cors_kwargs
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Welcome to Nales-It API"}
