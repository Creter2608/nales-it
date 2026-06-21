import fitz  # PyMuPDF
from typing import List
from fastapi import UploadFile

async def extract_text_from_pdf(file: UploadFile, pages_per_chunk: int = 15) -> List[str]:
    """
    Trích xuất văn bản từ file PDF và chia thành các cụm (chunks) để xử lý song song.
    """
    content = await file.read()
    doc = fitz.open(stream=content, filetype="pdf")
    
    chunks = []
    current_chunk_text = ""
    
    for i, page in enumerate(doc):
        current_chunk_text += page.get_text() + "\n"
        if (i + 1) % pages_per_chunk == 0:
            chunks.append(current_chunk_text.strip())
            current_chunk_text = ""
            
    if current_chunk_text.strip():
        chunks.append(current_chunk_text.strip())
    
    # Khôi phục vị trí con trỏ của file nếu cần đọc lại
    await file.seek(0)
    return chunks

import base64

async def extract_images_from_pdf(file: UploadFile, pages_per_chunk: int = 15) -> List[List[str]]:
    """
    Chụp ảnh từng trang PDF và chia thành cụm (chunks).
    Trả về danh sách các cụm, mỗi cụm chứa danh sách các chuỗi base64 ảnh.
    """
    content = await file.read()
    doc = fitz.open(stream=content, filetype="pdf")
    
    chunks = []
    current_chunk_images = []
    
    for i, page in enumerate(doc):
        pix = page.get_pixmap(dpi=150)
        img_bytes = pix.tobytes("png")
        img_b64 = base64.b64encode(img_bytes).decode("utf-8")
        current_chunk_images.append(img_b64)
        
        if (i + 1) % pages_per_chunk == 0:
            chunks.append(current_chunk_images)
            current_chunk_images = []
            
    if current_chunk_images:
        chunks.append(current_chunk_images)
        
    await file.seek(0)
    return chunks
