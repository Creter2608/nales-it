import fitz  # PyMuPDF
from typing import List
from fastapi import UploadFile

import tempfile
import os
import logging
import opendataloader_pdf
import base64
import asyncio

logger = logging.getLogger(__name__)

def _sync_extract_text(temp_pdf_path: str, pages_per_chunk: int) -> List[str]:
    """Synchronous core for opendataloader extraction."""
    output_dir = os.path.join(os.path.dirname(temp_pdf_path), "output")
    os.makedirs(output_dir, exist_ok=True)
    
    opendataloader_pdf.convert(
        input_path=[temp_pdf_path],
        output_dir=output_dir,
        format="markdown"
    )
    
    md_files = [f for f in os.listdir(output_dir) if f.endswith(".md")]
    if not md_files:
        raise Exception("Could not find Markdown file after conversion.")
        
    md_path = os.path.join(output_dir, md_files[0])
    with open(md_path, "r", encoding="utf-8") as f:
        markdown_text = f.read()
        
    chunks = []
    max_chars = 3000 * pages_per_chunk
    current_chunk = ""
    
    for paragraph in markdown_text.split("\n\n"):
        if len(current_chunk) + len(paragraph) > max_chars and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = paragraph + "\n\n"
        else:
            current_chunk += paragraph + "\n\n"
            
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
        
    return chunks

def _sync_fallback_extract_text(content: bytes, pages_per_chunk: int) -> List[str]:
    """Synchronous fallback using PyMuPDF."""
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
    return chunks

async def extract_text_from_pdf(file: UploadFile, pages_per_chunk: int = 15) -> List[str]:
    """
    Extract text from PDF file to Markdown format. Fallbacks to PyMuPDF if failed.
    """
    content = await file.read()
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            safe_filename = os.path.basename(file.filename or "temp.pdf")
            temp_pdf_path = os.path.join(temp_dir, safe_filename)
            with open(temp_pdf_path, "wb") as f:
                f.write(content)
                
            logger.info("Starting to extract PDF to Markdown using opendataloader-pdf in thread...")
            chunks = await asyncio.to_thread(_sync_extract_text, temp_pdf_path, pages_per_chunk)
            
            await file.seek(0)
            logger.info("Successfully extracted Markdown!")
            return chunks

    except Exception as e:
        logger.error(f"Error using opendataloader-pdf: {e}. Falling back to PyMuPDF in thread.")
        chunks = await asyncio.to_thread(_sync_fallback_extract_text, content, pages_per_chunk)
        await file.seek(0)
        return chunks

def _sync_extract_images(content: bytes, pages_per_chunk: int) -> List[List[str]]:
    doc = fitz.open(stream=content, filetype="pdf")
    chunks = []
    current_chunk_images = []
    
    for i, page in enumerate(doc):
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        img_bytes = pix.tobytes("png")
        img_b64 = base64.b64encode(img_bytes).decode('utf-8')
        current_chunk_images.append(img_b64)
        
        if (i + 1) % pages_per_chunk == 0:
            chunks.append(current_chunk_images)
            current_chunk_images = []
            
    if current_chunk_images:
        chunks.append(current_chunk_images)
    return chunks

async def extract_images_from_pdf(file: UploadFile, pages_per_chunk: int = 50) -> List[List[str]]:
    """
    Extract all PDF pages as base64 encoded images.
    """
    await file.seek(0)
    content = await file.read()
    chunks = await asyncio.to_thread(_sync_extract_images, content, pages_per_chunk)
    await file.seek(0)
    return chunks
