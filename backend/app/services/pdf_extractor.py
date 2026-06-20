import fitz  # PyMuPDF
from fastapi import UploadFile

async def extract_text_from_pdf(file: UploadFile) -> str:
    """
    Trích xuất toàn bộ văn bản từ file PDF.
    """
    content = await file.read()
    doc = fitz.open(stream=content, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    
    # Khôi phục vị trí con trỏ của file nếu cần đọc lại
    await file.seek(0)
    return text.strip()
