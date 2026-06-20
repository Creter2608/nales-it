import logging
import asyncio
from fastapi import APIRouter, File, UploadFile, HTTPException, BackgroundTasks
from app.services.pdf_extractor import extract_text_from_pdf
from app.services.quiz_generator import generate_quiz_from_text, solve_quiz_questions

logger = logging.getLogger(__name__)
upload_router = APIRouter()
# Gán upload_router = router để tương thích ngược với code cũ import router
router = upload_router

async def background_solve_chunking(quiz_id: str, remaining_unsolved: list):
    """
    Tiến trình ngầm: Chia nhỏ câu hỏi thành cụm 5 câu, giải và update MongoDB/MockDB.
    """
    if not remaining_unsolved:
        return
        
    logger.info(f"[Background Task] Bắt đầu giải ngầm {len(remaining_unsolved)} câu cho Quiz {quiz_id}")
    chunk_size = 5
    
    from app.db.mongodb import get_database
    db = get_database()
    
    for i in range(0, len(remaining_unsolved), chunk_size):
        chunk = remaining_unsolved[i:i + chunk_size]
        try:
            solved_results = await solve_quiz_questions(chunk)
            
            # Cập nhật DB
            if db is not None:
                from bson.objectid import ObjectId
                # Lấy bản ghi hiện tại
                quiz_data = await db["quizzes"].find_one({"_id": ObjectId(quiz_id)})
                if quiz_data:
                    solved_map = {str(item["id"]): item for item in solved_results}
                    for q in quiz_data["questions"]:
                        sid = str(q.get("id"))
                        if sid in solved_map:
                            q["correct_answer_id"] = solved_map[sid].get("correct_answer_id")
                            q["explanation"] = solved_map[sid].get("explanation")
                    await db["quizzes"].replace_one({"_id": ObjectId(quiz_id)}, quiz_data)
            else:
                # Mock DB update
                from app.api.quiz import MOCK_QUIZ_DB
                if quiz_id in MOCK_QUIZ_DB:
                    quiz_data = MOCK_QUIZ_DB[quiz_id]
                    solved_map = {str(item["id"]): item for item in solved_results}
                    for q in quiz_data["questions"]:
                        sid = str(q.get("id"))
                        if sid in solved_map:
                            q["correct_answer_id"] = solved_map[sid].get("correct_answer_id")
                            q["explanation"] = solved_map[sid].get("explanation")
                    MOCK_QUIZ_DB[quiz_id] = quiz_data
                    
            logger.info(f"[Background Task] Đã giải xong cụm {i//chunk_size + 1}. Đã lưu DB.")
            await asyncio.sleep(2) # Nghỉ 2 giây tránh Rate Limit
            
        except Exception as e:
            logger.error(f"[Background Task] Lỗi khi giải cụm câu hỏi: {e}")
            # Có thể thử lại hoặc bỏ qua, với MVP ta bỏ qua cụm lỗi.

@router.post("/pdf")
async def upload_pdf(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    try:
        # Bước 1
        logger.info(f"Nhận file: {file.filename}")
        pdf_bytes = await file.read()
        text = extract_text_from_pdf(pdf_bytes)
        
        # Bước 2: Gọi AI (chỉ giải 5 câu đầu)
        logger.info("Bắt đầu gửi văn bản cho Gemini AI (Tách 2 nhịp)...")
        quiz, remaining_unsolved = await generate_quiz_from_text(text)
        
        # Bước 3: Lưu Database (với 5 câu đầu đã giải)
        from app.db.mongodb import get_database
        db = get_database()
        if db is not None:
            quiz_dict = quiz.model_dump(exclude={"id"})
            result = await db["quizzes"].insert_one(quiz_dict)
            quiz.id = str(result.inserted_id)
        else:
            import uuid
            quiz.id = str(uuid.uuid4())
            from app.api.quiz import MOCK_QUIZ_DB
            quiz_dict = quiz.model_dump()
            quiz_dict["id"] = quiz.id
            MOCK_QUIZ_DB[quiz.id] = quiz_dict
            
        # Kích hoạt Background Task
        if remaining_unsolved:
            background_tasks.add_task(background_solve_chunking, quiz.id, remaining_unsolved)
            
        logger.info(f"Hoàn tất Upload! Trả về Quiz: {quiz.id}. Còn lại {len(remaining_unsolved)} câu đang chạy ngầm.")
        return quiz
    except ValueError as ve:
        raise HTTPException(status_code=422, detail=str(ve))
    except Exception as ve:
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Lỗi máy chủ (500): {str(ve)}")
