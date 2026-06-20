from pydantic import BaseModel, Field
from typing import List, Optional

class Answer(BaseModel):
    id: str = Field(description="Mã đáp án (ví dụ: A, B, C, D)")
    content: str = Field(description="Nội dung đáp án")

class Question(BaseModel):
    question_text: str = Field(description="Nội dung câu hỏi")
    options: List[Answer] = Field(description="Danh sách các lựa chọn đáp án")
    correct_answer_id: str = Field(description="Mã của đáp án đúng (ví dụ: A)")
    explanation: Optional[str] = Field(None, description="Giải thích chi tiết vì sao đáp án đó đúng (nếu có)")

class Quiz(BaseModel):
    title: str = Field(description="Tiêu đề của bài trắc nghiệm")
    questions: List[Question] = Field(description="Danh sách các câu hỏi")
