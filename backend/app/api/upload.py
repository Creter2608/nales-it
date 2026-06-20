from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.pdf_extractor import extract_text_from_pdf
from app.services.quiz_generator import generate_quiz_from_text
from app.schemas.quiz import Quiz
import logging

logger = logging.getLogger(__name__)
upload_router = APIRouter()

@upload_router.post("/upload/pdf", response_model=Quiz, tags=["upload"])
async def upload_pdf(file: UploadFile = File(...)):
    """
    API nhận file PDF, bóc tách chữ, gọi AI và trả về Quiz format JSON.
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Hiện tại hệ thống chỉ hỗ trợ xử lý file PDF.")
    
    try:
        # Bước 1: Trích xuất text từ PDF
        text = await extract_text_from_pdf(file)
        
        if not text:
            raise HTTPException(status_code=400, detail="File PDF trống hoặc không tìm thấy nội dung văn bản.")
            
        # Bước 2: Gọi Gemini AI để biến đổi text thành Quiz
        quiz = await generate_quiz_from_text(text)
        
        return quiz
    except ValueError as ve:
        raise HTTPException(status_code=422, detail=str(ve))
    except Exception as e:
        logger.error(f"Lỗi xử lý file: {e}")
        raise HTTPException(status_code=500, detail="Đã xảy ra lỗi nội bộ trong quá trình xử lý.")
