import logging
from fastapi import APIRouter, HTTPException
from bson.objectid import ObjectId
from app.db.mongodb import get_database
from app.schemas.quiz import Quiz

logger = logging.getLogger(__name__)
quiz_router = APIRouter()

MOCK_QUIZ_DB = {} # Dictionary lưu trữ tạm thời nếu MongoDB không hoạt động

@quiz_router.get("/{quiz_id}", response_model=Quiz)
async def get_quiz(quiz_id: str):
    """
    Lấy thông tin một bài Quiz đã lưu từ MongoDB hoặc Mock DB
    """
    db = get_database()
    if db is None:
        if quiz_id in MOCK_QUIZ_DB:
            return Quiz(**MOCK_QUIZ_DB[quiz_id])
        raise HTTPException(status_code=404, detail="Không tìm thấy bài Quiz.")
        
    try:
        obj_id = ObjectId(quiz_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID Quiz không hợp lệ.")
        
    quiz_data = await db["quizzes"].find_one({"_id": obj_id})
    if not quiz_data:
        raise HTTPException(status_code=404, detail="Không tìm thấy bài Quiz.")
        
    quiz_data["id"] = str(quiz_data["_id"])
    return Quiz(**quiz_data)

from pydantic import BaseModel
from typing import Dict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from app.core.config import settings

class GradeRequest(BaseModel):
    quiz_id: str
    user_answers: Dict[str, str] # Map từ question_id -> answer_id

class GradeResponse(BaseModel):
    score: int
    total: int
    ai_feedback: str

@quiz_router.post("/grade", response_model=GradeResponse)
async def grade_quiz(request: GradeRequest):
    """
    Chấm điểm bài làm và gọi AI để nhận xét tổng quan
    """
    db = get_database()
    if db is None:
        if request.quiz_id in MOCK_QUIZ_DB:
            quiz_data = MOCK_QUIZ_DB[request.quiz_id]
        else:
            raise HTTPException(status_code=404, detail="Không tìm thấy bài Quiz.")
    else:
        try:
            obj_id = ObjectId(request.quiz_id)
        except Exception:
            raise HTTPException(status_code=400, detail="ID Quiz không hợp lệ.")
        quiz_data = await db["quizzes"].find_one({"_id": obj_id})
    if not quiz_data:
        raise HTTPException(status_code=404, detail="Không tìm thấy bài Quiz.")
        
    quiz = Quiz(**quiz_data)
    
    # Tính điểm thủ công nếu câu hỏi có correct_answer_id
    score = 0
    total = len(quiz.questions)
    wrong_questions = []
    
    for q in quiz.questions:
        user_ans = request.user_answers.get(q.id)
        if q.correct_answer_id and user_ans == q.correct_answer_id:
            score += 1
        elif user_ans:
            wrong_questions.append({
                "question": q.content,
                "user_chose": user_ans,
                "correct_was": q.correct_answer_id
            })
            
    # Gửi cho AI nhận xét
    if not settings.GEMINI_API_KEY:
        feedback = "Chưa cấu hình API Key nên không thể tạo nhận xét."
    else:
        llm = ChatGoogleGenerativeAI(
            model="gemini-3.1-pro-preview", 
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.7,
        )
        prompt = PromptTemplate(
            input_variables=["score", "total", "wrong_list"],
            template="""
Học sinh vừa làm xong bài kiểm tra và đạt {score}/{total} điểm.
Danh sách các câu học sinh làm sai:
{wrong_list}

Với tư cách là một gia sư AI thân thiện, hãy viết một đoạn nhận xét ngắn gọn (khoảng 3-4 câu) để:
1. Khen ngợi sự cố gắng.
2. Chỉ ra điểm yếu chung dựa trên các câu làm sai (nếu có).
3. Động viên học sinh.
Không cần giải chi tiết từng câu, chỉ nhận xét tổng quan.
"""
        )
        chain = prompt | llm
        wrong_list_str = "\n".join([f"- Câu: {w['question']} | Chọn sai: {w['user_chose']} | Đáp án đúng: {w['correct_was']}" for w in wrong_questions])
        if not wrong_list_str:
            wrong_list_str = "Học sinh làm đúng 100%!"
            
        try:
            res = await chain.ainvoke({"score": score, "total": total, "wrong_list": wrong_list_str})
            feedback = res.content
        except Exception as e:
            logger.error(f"Lỗi khi gọi AI chấm bài: {e}")
            feedback = "Rất tiếc, AI đang bận nên không thể đưa ra nhận xét lúc này."
            
    return GradeResponse(score=score, total=total, ai_feedback=feedback)

class ResolveRequest(BaseModel):
    quiz_id: str
    question_id: str

@quiz_router.post("/resolve")
async def resolve_question(request: ResolveRequest):
    """
    Giải lại 1 câu hỏi cụ thể theo yêu cầu của học sinh (Cờ đỏ 🚩)
    """
    db = get_database()
    # Tìm Quiz
    if db is None:
        if request.quiz_id in MOCK_QUIZ_DB:
            quiz_data = MOCK_QUIZ_DB[request.quiz_id]
        else:
            raise HTTPException(status_code=404, detail="Không tìm thấy bài Quiz.")
    else:
        try:
            obj_id = ObjectId(request.quiz_id)
            quiz_data = await db["quizzes"].find_one({"_id": obj_id})
        except Exception:
            raise HTTPException(status_code=400, detail="ID Quiz không hợp lệ.")
            
    if not quiz_data:
        raise HTTPException(status_code=404, detail="Không tìm thấy bài Quiz.")

    # Tìm Question
    target_q = None
    for q in quiz_data["questions"]:
        if str(q["id"]) == request.question_id:
            target_q = q
            break
            
    if not target_q:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu hỏi.")
        
    from app.services.quiz_generator import resolve_single_question
    
    try:
        new_result = await resolve_single_question(
            target_q["content"],
            target_q["answers"],
            target_q.get("correct_answer_id", ""),
            target_q.get("explanation", "")
        )
        target_q["correct_answer_id"] = new_result.get("correct_answer_id")
        target_q["explanation"] = new_result.get("explanation")
        
        # Save back
        if db is not None:
            await db["quizzes"].replace_one({"_id": obj_id}, quiz_data)
        else:
            MOCK_QUIZ_DB[request.quiz_id] = quiz_data
            
        return {"status": "success", "new_answer": target_q["correct_answer_id"], "new_explanation": target_q["explanation"]}
    except Exception as e:
        logger.error(f"Lỗi giải lại câu hỏi: {e}")
        raise HTTPException(status_code=500, detail="Không thể giải lại câu hỏi lúc này.")
