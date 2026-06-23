import asyncio
import os
import sys

# Thêm đường dẫn backend vào sys.path để import app.services
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import UploadFile
from app.services.pdf_extractor import extract_text_from_pdf

async def test():
    with open("test_exam.pdf", "rb") as f:
        # Mock UploadFile
        class MockUploadFile(UploadFile):
            def __init__(self, file, filename):
                self.file = file
                self.filename = filename
            async def read(self):
                return self.file.read()
            async def seek(self, pos):
                self.file.seek(pos)
                
        file = MockUploadFile(file=f, filename="test_exam.pdf")
        chunks = await extract_text_from_pdf(file)
        print("Total chunks:", len(chunks))
        for i, chunk in enumerate(chunks):
            print(f"--- Chunk {i} ---")
            print(chunk[:500])
            print("...")

if __name__ == "__main__":
    asyncio.run(test())
