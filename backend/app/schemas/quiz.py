from pydantic import BaseModel, Field
from typing import List, Optional

class Answer(BaseModel):
    id: str = Field(..., description="Answer ID, e.g., 'A', 'B', 'C', 'D'")
    content: str = Field(..., description="Content of the answer")

class Question(BaseModel):
    id: str = Field(..., description="Question ID, e.g., '1', '2', '3'")
    content: str = Field(..., description="Content of the question")
    answers: List[Answer] = Field(..., description="List of available answers (A, B, C, D)")
    correct_answer_id: Optional[str] = Field(None, description="ID of the correct answer. Null if no answer is provided.")
    explanation: Optional[str] = Field(None, description="Explanation for the correct answer. Null if not provided.")
    shared_context: Optional[str] = Field(None, description="Shared context or passage for a group of questions.")
    image_base64: Optional[str] = Field(None, description="Base64 string of the attached image for this question.")

class Quiz(BaseModel):
    id: Optional[str] = Field(None, description="Database ID of the quiz (MongoDB Object ID)")
    title: str = Field(..., description="Title of the quiz")
    questions: List[Question] = Field(..., description="List of questions in the quiz")
