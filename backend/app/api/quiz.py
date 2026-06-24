import logging
from fastapi import APIRouter, HTTPException, Depends
from bson.objectid import ObjectId
from pydantic import BaseModel
from typing import Dict
from langchain_core.prompts import PromptTemplate

from app.db.mongodb import get_database
from app.db.mock import get_mock_quiz, set_mock_quiz
from app.schemas.quiz import Quiz
from app.core.config import settings
from app.core.auth import verify_api_key

logger = logging.getLogger(__name__)
quiz_router = APIRouter(prefix="/quiz", tags=["quiz"], dependencies=[Depends(verify_api_key)])

@quiz_router.get("/{quiz_id}", response_model=Quiz)
async def get_quiz(quiz_id: str):
    """
    Get quiz information from MongoDB or Mock DB.
    """
    quiz_data = await _get_quiz_data(quiz_id)
    quiz_data["id"] = str(quiz_data.get("_id", quiz_data.get("id")))
    return Quiz(**quiz_data)

@quiz_router.get("/{quiz_id}/question/{idx}")
async def get_quiz_question(quiz_id: str, idx: int):
    """
    Get a specific question by index from the quiz.
    Useful to avoid re-fetching the entire quiz.
    """
    quiz_data = await _get_quiz_data(quiz_id)
    questions = quiz_data.get("questions", [])
    if idx < 0 or idx >= len(questions):
        raise HTTPException(status_code=404, detail="Question not found at this index.")
    return questions[idx]

async def _get_quiz_data(quiz_id: str) -> dict:
    db = get_database()
    if db is None:
        quiz_data = get_mock_quiz(quiz_id)
        if not quiz_data:
            raise HTTPException(status_code=404, detail="Quiz not found.")
        return quiz_data
        
    try:
        obj_id = ObjectId(quiz_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid Quiz ID.")
        
    quiz_data = await db["quizzes"].find_one({"_id": obj_id})
    if not quiz_data:
        raise HTTPException(status_code=404, detail="Quiz not found.")
        
    return quiz_data


class GradeRequest(BaseModel):
    quiz_id: str
    user_answers: Dict[str, str] # Map from question_id -> answer_id

class GradeResponse(BaseModel):
    score: int
    total: int
    ai_feedback: str

@quiz_router.post("/grade", response_model=GradeResponse)
async def grade_quiz(request: GradeRequest):
    """
    Grade the quiz and call AI for overall feedback.
    """
    quiz_data = await _get_quiz_data(request.quiz_id)
    quiz_data["id"] = str(quiz_data.get("_id", quiz_data.get("id")))
        
    quiz = Quiz(**quiz_data)
    
    # Calculate score manually
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
            
    # Send to AI for feedback
    if not settings.ai_enabled:
        feedback = "No AI backend configured, cannot generate feedback."
    else:
        from app.services.quiz_generator import generate_feedback
        feedback = await generate_feedback(score, total, wrong_questions)
            
    return GradeResponse(score=score, total=total, ai_feedback=feedback)

class ResolveRequest(BaseModel):
    quiz_id: str
    question_id: str
    force: bool = False

@quiz_router.post("/resolve")
async def resolve_question(request: ResolveRequest):
    """
    Resolve a specific question per student request (Red flag 🚩).
    """
    db = get_database()
    # Find Quiz
    quiz_data = await _get_quiz_data(request.quiz_id)

    # Find Question
    target_q = None
    for q in quiz_data["questions"]:
        if str(q["id"]) == request.question_id:
            target_q = q
            break
            
    if not target_q:
        raise HTTPException(status_code=404, detail="Question not found.")
        
    # If not forcing and it's already solved, just return it
    if not request.force and target_q.get("correct_answer_id"):
        return {"status": "success", "new_answer": target_q["correct_answer_id"], "new_explanation": target_q.get("explanation", "")}
        
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
            obj_id = ObjectId(request.quiz_id)
            await db["quizzes"].replace_one({"_id": obj_id}, quiz_data)
        else:
            set_mock_quiz(request.quiz_id, quiz_data)
            
        return {"status": "success", "new_answer": target_q["correct_answer_id"], "new_explanation": target_q["explanation"]}
    except Exception as e:
        logger.error(f"Error re-solving question: {e}")
        raise HTTPException(status_code=500, detail="Cannot resolve question at this time.")
