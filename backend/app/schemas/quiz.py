from pydantic import BaseModel, Field
from typing import List, Optional

class Answer(BaseModel):
    id: str = Field(..., description="ID của đáp án, ví dụ: 'A', 'B', 'C', 'D'")
    content: str = Field(..., description="Nội dung của đáp án")

class Question(BaseModel):
    id: str = Field(..., description="ID của câu hỏi, ví dụ: '1', '2', '3'")
    content: str = Field(..., description="Nội dung câu hỏi")
    answers: List[Answer] = Field(..., description="Danh sách các đáp án (A, B, C, D)")
    correct_answer_id: Optional[str] = Field(None, description="ID của đáp án đúng. Có thể null nếu không có đáp án.")
    explanation: Optional[str] = Field(None, description="Giải thích tại sao lại chọn đáp án này. Có thể null.")
    shared_context: Optional[str] = Field(None, description="Thông tin dùng chung cho một cụm câu hỏi.")
    image_base64: Optional[str] = Field(None, description="Ảnh đính kèm cho câu hỏi dưới dạng chuỗi base64.")

class Quiz(BaseModel):
    id: Optional[str] = Field(None, description="ID của bài trắc nghiệm trong database (MongoDB Object ID)")
    title: str = Field(..., description="Tiêu đề của bài trắc nghiệm")
    questions: List[Question] = Field(..., description="Danh sách các câu hỏi")
