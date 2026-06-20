from fastapi import APIRouter
from app.api.upload import upload_router
from app.api.quiz import quiz_router

api_router = APIRouter()

@api_router.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "message": "Nales-It API is running"}

# Đăng ký upload API
api_router.include_router(upload_router)
api_router.include_router(quiz_router)
