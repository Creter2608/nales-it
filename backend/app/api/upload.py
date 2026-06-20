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
        logger.info(f"Đã nhận yêu cầu tải lên file: {file.filename}")
        
        # Bước 1: Trích xuất text từ PDF
        logger.info("Đang bóc tách văn bản từ PDF...")
        text = await extract_text_from_pdf(file)
        
        if not text:
            logger.warning(f"File {file.filename} không chứa văn bản hợp lệ.")
            raise HTTPException(status_code=400, detail="File PDF trống hoặc không tìm thấy nội dung văn bản.")
            
        logger.info(f"Bóc tách thành công! Tổng số ký tự tìm thấy: {len(text)}")
            
        # Bước 2: Gọi Gemini AI để biến đổi text thành Quiz
        logger.info("Bắt đầu gửi văn bản cho Gemini AI xử lý... Quá trình này có thể mất thời gian.")
        quiz = await generate_quiz_from_text(text)
        
        # Bước 3: Lưu Quiz vào MongoDB
        from app.db.mongodb import get_database
        db = get_database()
        if db is not None:
            logger.info("Đang lưu Quiz vào MongoDB...")
            quiz_dict = quiz.model_dump(exclude={"id"}) # Bỏ field id rỗng để Mongo tự sinh _id
            result = await db["quizzes"].insert_one(quiz_dict)
            quiz.id = str(result.inserted_id)
            logger.info(f"Lưu Database thành công! Quiz ID: {quiz.id}")
        else:
            logger.warning("CẢNH BÁO: Không có kết nối MongoDB, bài Quiz chưa được lưu.")
            
        logger.info(f"Hoàn tất quá trình! Tiêu đề: '{quiz.title}' với {len(quiz.questions)} câu hỏi.")
        return quiz
    except ValueError as ve:
        raise HTTPException(status_code=422, detail=str(ve))
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Lỗi xử lý file:\n{error_details}")
        raise HTTPException(status_code=500, detail=f"Lỗi máy chủ (500): {str(e)}")
