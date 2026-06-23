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

async def extract_text_from_pdf(file: UploadFile, pages_per_chunk: int = 5) -> tuple[List[str], dict]:
    """
    Extract text and images from PDF file using PyMuPDF.
    Returns: (chunks_list, image_mapping_dict)
    """
    content = await file.read()
    
    def _extract() -> tuple[List[str], dict]:
        doc = fitz.open(stream=content, filetype="pdf")
        chunks = []
        image_mapping = {}
        global_img_idx = 0
        
        current_chunk_text = ""
        
        for i, page in enumerate(doc):
            blocks = page.get_text("dict")["blocks"]
            blocks.sort(key=lambda b: (b["bbox"][1], b["bbox"][0])) # Sort by Y, then X
            
            for block in blocks:
                if block["type"] == 0:  # Text
                    for line in block["lines"]:
                        for span in line["spans"]:
                            current_chunk_text += span["text"]
                        current_chunk_text += "\n"
                    current_chunk_text += "\n"
                elif block["type"] == 1:  # Image
                    img_data = block.get("image")
                    if img_data:
                        b64 = base64.b64encode(img_data).decode('utf-8')
                        img_tag = f"[IMAGE_{global_img_idx}]"
                        image_mapping[img_tag] = b64
                        current_chunk_text += f"\n\n{img_tag}\n\n"
                        global_img_idx += 1
                        
            if (i + 1) % pages_per_chunk == 0:
                chunks.append(current_chunk_text.strip())
                current_chunk_text = ""
                
        if current_chunk_text.strip():
            chunks.append(current_chunk_text.strip())
            
        return chunks, image_mapping

    logger.info("Starting to extract PDF using PyMuPDF (Hybrid Text+Image)...")
    return await asyncio.to_thread(_extract)

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
