import asyncio
import os
import sys
from dotenv import load_dotenv

load_dotenv()
from app.services.quiz_generator import generate_quiz_from_text

async def main():
    text = """
    Trường Đại học Bách khoa-ĐHQG TPHCM Khoa Khoa học Ứng dụng
    Thi cuối kỳ Kỳ/năm học 241 2024-2025
    Ngày thi 24/12/2024
    Môn học GIẢI TÍCH 1
    Câu 1. (L.O.1) Cho f(x) = 1/sqrt(1 + 2x). Dùng xấp xỉ tuyến tính của f(x) tại x0 = 0 để tính gần đúng f(-0.1) ta được kết quả là
    A 1.1372 B Các câu khác sai. C 1.0863
    D 1.0763 E 1.1000
    """
    chunks = [text]
    try:
        quiz, remaining = await generate_quiz_from_text(chunks)
        print("Success!")
        print("Quiz ID:", quiz.id)
        print("Questions extracted:", len(quiz.questions))
        print("Remaining:", len(remaining))
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
