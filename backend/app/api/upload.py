import logging
import asyncio
from fastapi import APIRouter, File, UploadFile, HTTPException, BackgroundTasks
from app.services.pdf_extractor import extract_text_from_pdf
from app.services.quiz_solver import solve_quiz_questions
from fastapi.responses import StreamingResponse
import json
import os

logger = logging.getLogger(__name__)
upload_router = APIRouter(prefix="/upload", tags=["upload"])
router = upload_router

async def background_solve_chunking(quiz_id: str, remaining_unsolved: list):
    """
    Background task: Chunk questions into groups of 5, solve, and update MongoDB/MockDB.
    """
    if not remaining_unsolved:
        return
        
    logger.info(f"[Background Task] Starting to solve {len(remaining_unsolved)} questions for Quiz {quiz_id}")
    chunk_size = 5
    
    from app.db.mongodb import get_database
    from app.db.mock import get_mock_quiz, set_mock_quiz
    db = get_database()
    
    for i in range(0, len(remaining_unsolved), chunk_size):
        chunk = remaining_unsolved[i:i + chunk_size]
        try:
            solved_results = await solve_quiz_questions(chunk)
            
            # Update DB
            if db is not None:
                from bson.objectid import ObjectId
                # Get current record
                quiz_data = await db["quizzes"].find_one({"_id": ObjectId(quiz_id)})
                if quiz_data:
                    solved_map = {str(item["id"]): item for item in solved_results}
                    set_updates = {}
                    for i, q in enumerate(quiz_data["questions"]):
                        if str(q["id"]) in solved_map:
                            solved_q = solved_map[str(q["id"])]
                            prefix = f"questions.{i}."
                            set_updates[prefix + "content"] = solved_q.get("content", q.get("content", ""))
                            set_updates[prefix + "answers"] = solved_q.get("answers", q.get("answers", []))
                            set_updates[prefix + "correct_answer_id"] = solved_q.get("correct_answer_id", None)
                            set_updates[prefix + "explanation"] = solved_q.get("explanation", None)
                    
                    if set_updates:
                        await db["quizzes"].update_one({"_id": ObjectId(quiz_id)}, {"$set": set_updates})
            else:
                # Mock DB update
                quiz_data = get_mock_quiz(quiz_id)
                if quiz_data:
                    solved_map = {str(item["id"]): item for item in solved_results}
                    for q in quiz_data["questions"]:
                        sid = str(q.get("id"))
                        if sid in solved_map:
                            q["correct_answer_id"] = solved_map[sid].get("correct_answer_id")
                            q["explanation"] = solved_map[sid].get("explanation")
                    set_mock_quiz(quiz_id, quiz_data)
                    
            logger.info(f"[Background Task] Finished solving chunk {i//chunk_size + 1}. Saved to DB.")
            await asyncio.sleep(2) # Sleep for 2 seconds to avoid Rate Limit
            
        except Exception as e:
            logger.error(f"[Background Task] Error solving question chunk: {e}")
            # For MVP, we ignore the failed chunk and continue to the next one.
            continue


@router.post("/pdf")
async def upload_pdf(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.pdf') and file.content_type != 'application/pdf':
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF files are allowed.")
        
    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)
    if file_size > 50 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 50MB.")

    async def event_generator():
        try:
            logger.info(f"Received file: {file.filename}")
            chunks, image_mapping = await extract_text_from_pdf(file)
            
            logger.info(f"Started SSE stream from {len(chunks)} chunk(s)...")
            from app.services.quiz_extractor import stream_quiz_from_pdf
            
            queue = asyncio.Queue()
            
            async def run_generator():
                try:
                    async for ev in stream_quiz_from_pdf(chunks, image_mapping, file=file):
                        await queue.put(ev)
                except Exception as e:
                    import traceback
                    logger.error(traceback.format_exc())
                    await queue.put({"type": "error", "detail": "Lỗi trong quá trình AI phân tích. Vui lòng thử lại."})
                finally:
                    await queue.put(None)
                    
            # Bắt đầu chạy generator ở chế độ ngầm
            generator_task = asyncio.create_task(run_generator())
            
            try:
                while True:
                    try:
                        # Timeout every 15s to send a heartbeat (progress) without killing the generator
                        event = await asyncio.wait_for(queue.get(), timeout=15.0)
                        if event is None:
                            break
                    except asyncio.TimeoutError:
                        yield f"data: {json.dumps({'type': 'progress', 'message': 'Đang đợi AI phân tích dữ liệu...'}, ensure_ascii=False)}\n\n"
                        continue

                    if event["type"] == "done":
                        logger.info("YIELDING EVENT: done")
                        quiz_data = event.pop("quiz_data")
                        remaining_unsolved = event.pop("unsolved")
                        
                        from app.db.mongodb import get_database
                        db = get_database()
                        quiz_id = None
                        if db is not None:
                            result = await db["quizzes"].insert_one(quiz_data)
                            quiz_id = str(result.inserted_id)
                        else:
                            quiz_id = "local_" + "".join(random.choices(string.ascii_letters + string.digits, k=10))
                            from app.db.mock import set_mock_quiz
                            quiz_data["id"] = quiz_id
                            set_mock_quiz(quiz_id, quiz_data)
                            
                        event["quiz_id"] = quiz_id
                        
                        # Trigger Background Task
                        if remaining_unsolved:
                            background_tasks.add_task(background_solve_chunking, quiz_id, remaining_unsolved)
                            
                        yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                    else:
                        logger.info(f"YIELDING EVENT: {event.get('type')}")
                        yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            except asyncio.CancelledError:
                logger.warning("Client disconnected from SSE stream! Cancelling background LLM generation...")
                generator_task.cancel()
                raise
                    
        except Exception as e:
            import traceback
            logger.error(traceback.format_exc())
            error_event = {"type": "error", "detail": "An unexpected error occurred while processing the file. Please try again."}
            yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
