import logging
from fastapi import APIRouter, HTTPException
from bson.objectid import ObjectId
from app.db.mongodb import get_database
from app.schemas.quiz import Quiz

logger = logging.getLogger(__name__)
quiz_router = APIRouter()

@quiz_router.get("/{quiz_id}", response_model=Quiz)
async def get_quiz(quiz_id: str):
    """
    Lấy thông tin một bài Quiz đã lưu từ MongoDB
    """
    try:
        obj_id = ObjectId(quiz_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID Quiz không hợp lệ.")
        
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Lỗi kết nối cơ sở dữ liệu.")
        
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
    try:
        obj_id = ObjectId(request.quiz_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID Quiz không hợp lệ.")
        
    db = get_database()
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
