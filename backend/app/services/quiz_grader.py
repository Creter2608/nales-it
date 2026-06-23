"""Quiz grading and AI feedback generation."""

import logging
from langchain_core.prompts import PromptTemplate
from app.services.llm_utils import get_llm

logger = logging.getLogger(__name__)


async def generate_feedback(score: int, total: int, wrong_questions: list) -> str:
    """Generate AI tutor feedback based on quiz results."""
    llm = get_llm(temperature=0.7)
    prompt = PromptTemplate(
        input_variables=["score", "total", "wrong_list"],
        template="""
The student just finished the test and scored {score}/{total}.
List of questions the student answered incorrectly:
{wrong_list}

As a friendly AI tutor, write a short feedback paragraph (about 3-4 sentences) to:
1. Praise their effort.
2. Point out general weaknesses based on the incorrect answers (if any).
3. Encourage the student.
Do not explain each question in detail, just provide overall feedback.
"""
    )
    chain = prompt | llm
    wrong_list_str = "\n".join([
        f"- Question: {w['question']} | Chose incorrectly: {w['user_chose']} | Correct answer: {w['correct_was']}"
        for w in wrong_questions
    ])
    if not wrong_list_str:
        wrong_list_str = "Student got 100% correct!"

    try:
        res = await chain.ainvoke({"score": score, "total": total, "wrong_list": wrong_list_str})
        return res.content
    except Exception as e:
        logger.error(f"Error calling AI for grading: {e}")
        return "AI is currently unavailable to provide feedback."
