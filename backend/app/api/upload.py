import logging
import asyncio
from fastapi import APIRouter, File, UploadFile, HTTPException, BackgroundTasks
from app.services.pdf_extractor import extract_text_from_pdf
from app.services.quiz_generator import generate_quiz_from_text, solve_quiz_questions

logger = logging.getLogger(__name__)
upload_router = APIRouter(prefix="/upload", tags=["upload"])
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

from fastapi.responses import StreamingResponse
import json

@router.post("/pdf")
async def upload_pdf(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    async def event_generator():
        try:
            logger.info(f"Nhận file: {file.filename}")
            chunks = await extract_text_from_pdf(file)
            
            logger.info(f"Bắt đầu stream SSE từ {len(chunks)} chunk(s)...")
            from app.services.quiz_generator import stream_quiz_from_pdf
            
            async for event in stream_quiz_from_pdf(chunks, file=file):
                if event["type"] == "done":
                    # Lưu Database
                    quiz_data = event.pop("quiz_data")
                    remaining_unsolved = event.pop("unsolved")
                    
                    from app.db.mongodb import get_database
                    db = get_database()
                    quiz_id = None
                    if db is not None:
                        result = await db["quizzes"].insert_one(quiz_data)
                        quiz_id = str(result.inserted_id)
                    else:
                        import uuid
                        quiz_id = str(uuid.uuid4())
                        from app.api.quiz import MOCK_QUIZ_DB
                        quiz_data["id"] = quiz_id
                        MOCK_QUIZ_DB[quiz_id] = quiz_data
                        
                    event["quiz_id"] = quiz_id
                    
                    # Kích hoạt Background Task
                    if remaining_unsolved:
                        background_tasks.add_task(background_solve_chunking, quiz_id, remaining_unsolved)
                        
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                else:
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                    
        except Exception as e:
            import traceback
            logger.error(traceback.format_exc())
            error_event = {"type": "error", "detail": f"Lỗi máy chủ: {str(e)}"}
            yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
