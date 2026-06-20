import json
import logging
from typing import List, Dict, Any
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings
from app.schemas.quiz import Quiz

logger = logging.getLogger(__name__)

def _parse_json_from_text(content: str) -> dict | list:
    content = content.strip()
    if content.startswith("```json"):
        content = content.replace("```json", "", 1)
    if content.startswith("```"):
        content = content.replace("```", "", 1)
    if content.endswith("```"):
        content = content[: -3]
    return json.loads(content.strip())

async def _extract_quiz_structure(text: str) -> dict:
    """Bước 1: Sử dụng Flash để bóc tách sườn JSON từ văn bản."""
    logger.info("Bước 1: Bóc tách cấu trúc bằng gemini-flash-latest...")
    llm = ChatGoogleGenerativeAI(
        model="gemini-flash-latest", 
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0.1,
    )
    
    prompt = PromptTemplate(
        input_variables=["text"],
        template="""
Bạn là một công cụ trích xuất dữ liệu. Hãy đọc văn bản tài liệu sau và trích xuất thành danh sách câu hỏi trắc nghiệm (Quiz).
LƯU Ý QUAN TRỌNG: 
- KHÔNG TỰ GIẢI ĐỀ. Nếu trong tài liệu KHÔNG GHI SẴN ĐÁP ÁN, hãy để `correct_answer_id` và `explanation` là null.
- Chỉ điền `correct_answer_id` nếu tài liệu CÓ SẴN đáp án (ví dụ có bảng đáp án, khoanh tròn).

Cấu trúc JSON mong đợi:
{{
    "title": "Tên bài kiểm tra",
    "questions": [
        {{
            "id": "1",
            "content": "Nội dung câu hỏi?",
            "answers": [
                {{"id": "A", "content": "Đáp án 1"}},
                {{"id": "B", "content": "Đáp án 2"}},
                {{"id": "C", "content": "Đáp án 3"}},
                {{"id": "D", "content": "Đáp án 4"}}
            ],
            "correct_answer_id": "A",
            "explanation": "Lời giải trong đề"
        }}
    ]
}}
        
Văn bản tài liệu:
{text}
"""
    )
    
    chain = prompt | llm
    response = await chain.ainvoke({"text": text})
    return _parse_json_from_text(response.content)

async def _solve_quiz_questions(unsolved_questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Bước 2: Sử dụng Pro để giải các câu hỏi chưa có đáp án."""
    if not unsolved_questions:
        return []
        
    logger.info(f"Bước 2: Giải {len(unsolved_questions)} câu hỏi bằng gemini-2.5-pro...")
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-pro", 
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0.2,
    )
    
    prompt = PromptTemplate(
        input_variables=["questions_json"],
        template="""
Bạn là một giáo viên xuất sắc. Dưới đây là danh sách các câu hỏi trắc nghiệm chưa có đáp án.
Hãy giải từng câu, tìm ra đáp án đúng và viết lời giải thích ngắn gọn, dễ hiểu.

Input JSON:
{questions_json}

Hãy trả về CHỈ MỘT MẢNG JSON hợp lệ chứa kết quả, tuyệt đối không có văn bản nào khác.
Cấu trúc JSON đầu ra mong đợi:
[
    {{
        "id": "1",
        "correct_answer_id": "B",
        "explanation": "Vì theo định luật..."
    }}
]
"""
    )
    
    chain = prompt | llm
    input_json = json.dumps(unsolved_questions, ensure_ascii=False)
    response = await chain.ainvoke({"questions_json": input_json})
    return _parse_json_from_text(response.content)

async def generate_quiz_from_text(text: str) -> Quiz:
    """
    Hệ thống AI 2 Bước:
    Bước 1: Dùng Flash để trích xuất cấu trúc.
    Bước 2: Dùng Pro để giải đề (nếu cần).
    """
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY chưa được cấu hình!")
        
    try:
        # Nhịp 1: Trích xuất cấu trúc
        quiz_data = await _extract_quiz_structure(text)
        
        # Lọc ra các câu chưa có đáp án
        unsolved = []
        for q in quiz_data.get("questions", []):
            if not q.get("correct_answer_id"):
                unsolved.append({
                    "id": q.get("id"),
                    "content": q.get("content"),
                    "answers": q.get("answers")
                })
                
        # Nhịp 2: Giải đề (nếu cần)
        if unsolved:
            solved_results = await _solve_quiz_questions(unsolved)
            # Map kết quả giải về lại quiz_data
            solved_map = {str(item["id"]): item for item in solved_results}
            for q in quiz_data["questions"]:
                sid = str(q.get("id"))
                if sid in solved_map:
                    q["correct_answer_id"] = solved_map[sid].get("correct_answer_id")
                    q["explanation"] = solved_map[sid].get("explanation")
                    
        return Quiz(**quiz_data)
        
    except Exception as e:
        logger.error(f"Lỗi trong quá trình tạo Quiz 2 bước: {e}")
        raise ValueError(f"Không thể xử lý văn bản thành Quiz: {e}")
