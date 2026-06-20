import json
import logging
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings
from app.schemas.quiz import Quiz

logger = logging.getLogger(__name__)

async def generate_quiz_from_text(text: str) -> Quiz:
    """
    Gọi Gemini API để xử lý văn bản thô thành một đối tượng Quiz JSON.
    """
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY chưa được cấu hình!")

    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash-latest", 
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0.2, # Giữ temperature thấp để kết quả ổn định và đúng format
    )
    
    prompt = PromptTemplate(
        input_variables=["text"],
        template="""
Bạn là một chuyên gia giáo dục. Hãy đọc văn bản tài liệu sau và trích xuất thành một bài trắc nghiệm (Quiz).
Trả về KẾT QUẢ ĐẦU RA hoàn toàn dưới dạng JSON hợp lệ tuân thủ chặt chẽ cấu trúc sau, không kèm theo bất kỳ văn bản giải thích nào khác.
        
Cấu trúc JSON mong đợi:
{{
    "title": "Tên bài kiểm tra",
    "questions": [
        {{
            "question_text": "Nội dung câu hỏi?",
            "options": [
                {{"id": "A", "content": "Đáp án 1"}},
                {{"id": "B", "content": "Đáp án 2"}}
            ],
            "correct_answer_id": "A",
            "explanation": "Giải thích ngắn gọn"
        }}
    ]
}}
        
Văn bản tài liệu:
{text}
"""
    )
    
    chain = prompt | llm
    response = await chain.ainvoke({"text": text})
    
    # Tiền xử lý kết quả trả về để đảm bảo định dạng JSON hợp lệ
    content = response.content.strip()
    if content.startswith("```json"):
        content = content.replace("```json", "", 1)
    if content.endswith("```"):
        content = content[: -3]
        
    try:
        data = json.loads(content.strip())
        return Quiz(**data)
    except Exception as e:
        logger.error(f"Lỗi parse JSON: {content}")
        raise ValueError(f"Không thể parse kết quả từ AI thành JSON: {e}")
