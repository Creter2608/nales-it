"""Quiz extraction from PDF — main streaming pipeline."""

import logging
import asyncio
from typing import AsyncGenerator

from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage
from app.core.config import settings
from app.services.llm_utils import get_llm, parse_json_from_text
from app.services.quiz_solver import prescan_answer_keys

logger = logging.getLogger(__name__)

# JSON schema for quiz extraction (shared between text and vision paths)
QUIZ_EXTRACTION_SCHEMA = {
    "name": "quiz_extraction",
    "schema": {
        "type": "object",
        "properties": {
            "questions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "description": "Text of the question"},
                        "answers": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "string", "description": "A, B, C, D..."},
                                    "content": {"type": "string"}
                                },
                                "required": ["id", "content"],
                                "additionalProperties": False
                            }
                        }
                    },
                    "required": ["content", "answers"],
                    "additionalProperties": False
                }
            }
        },
        "required": ["questions"],
        "additionalProperties": False
    },
    "strict": True
}


def _normalize_questions(chunk_data: dict, image_mapping: dict,
                         prescan_keys: dict, unsolved: list,
                         global_question_id_ref: list) -> list:
    """Normalize and assign IDs to extracted questions.

    Args:
        global_question_id_ref: Single-element list used as a mutable counter reference.
    """
    chunk_questions = []

    if chunk_data.get("answer_keys"):
        prescan_keys.update(chunk_data["answer_keys"])

    for q in chunk_data.get("questions", []):
        if not q.get("content"):
            continue
        valid_answers = [a for a in q.get("answers", []) if a.get("id") and a.get("content")]
        if not valid_answers:
            continue

        q["answers"] = valid_answers
        q["content"] = str(q["content"])
        q["original_id"] = str(q.get("id", ""))
        q["id"] = str(global_question_id_ref[0])

        # Attach image if present
        if image_mapping:
            content = q["content"]
            q["image_base64"] = None
            for img_tag, b64 in image_mapping.items():
                if img_tag in content:
                    q["image_base64"] = b64
                    q["content"] = content.replace(img_tag, "").strip()
                    break

        ans = prescan_keys.get(q["original_id"]) or prescan_keys.get(str(global_question_id_ref[0]))
        if ans:
            q["correct_answer_id"] = ans
        else:
            unsolved.append(q)

        global_question_id_ref[0] += 1
        chunk_questions.append(q)

    return chunk_questions


async def stream_quiz_from_pdf(chunks: list[str], image_mapping: dict = None, file=None) -> AsyncGenerator[dict, None]:
    """Process PDF chunks concurrently and yield progress and partial results."""
    if not settings.ai_enabled:
        raise ValueError("No AI backend configured! Set LM_STUDIO_API_BASE or GEMINI_API_KEY.")

    yield {"type": "progress", "message": "Đang kiểm tra và quét bảng đáp án..."}
    prescan_keys = {}
    if chunks:
        prescan_keys = await prescan_answer_keys(chunks[-1])
        if prescan_keys:
            logger.info(f"Pre-scan found {len(prescan_keys)} answers.")

    llm = get_llm(temperature=0.1)

    prompt = PromptTemplate(
        input_variables=["text"],
        template_format="jinja2",
        template="""
You are a data extraction tool. Please read the following document text and extract multiple-choice questions.
IMPORTANT NOTES:
- You MUST output ONLY valid JSON.
- If you see an image placeholder like `[IMAGE_0]`, `[IMAGE_1]` in the text, you MUST include it inside the `content` of the question so we know which question it belongs to.
- For Mathematical formulas, wrap them in `$$` (e.g., `$$\\\\frac{1}{2}$$`).
- DO NOT solve the test. Do not output the correct answer or explanation.
- VERY IMPORTANT: Do NOT write long reasoning blocks. Output ONLY the JSON array.

Document text:
{{ text }}
"""
    )

    chain = prompt | llm.bind(response_format={"type": "json_schema", "json_schema": QUIZ_EXTRACTION_SCHEMA})
    sem = asyncio.Semaphore(3)

    async def process_text_chunk(chunk_idx, text):
        async with sem:
            try:
                res = await chain.ainvoke({"text": text})
                logger.warning(f"RAW LLM OUTPUT (Chunk {chunk_idx}):\n{res.content}\n---")

                parsed_json = parse_json_from_text(res.content)
                questions_list = []
                if isinstance(parsed_json, list):
                    questions_list = parsed_json
                elif isinstance(parsed_json, dict) and "questions" in parsed_json:
                    questions_list = parsed_json["questions"]

                if image_mapping and questions_list:
                    for q in questions_list:
                        content = q.get("content", "")
                        q["image_base64"] = None
                        for img_tag, b64 in image_mapping.items():
                            if img_tag in content:
                                q["image_base64"] = b64
                                q["content"] = content.replace(img_tag, "").strip()
                                break

                return chunk_idx, {"title": "Untitled Quiz", "questions": questions_list}
            except Exception as e:
                logger.error(f"Error processing text chunk {chunk_idx}: {e}")
                return chunk_idx, {}

    tasks = [asyncio.create_task(process_text_chunk(i, text)) for i, text in enumerate(chunks)]

    merged_quiz = {"title": "Untitled Quiz", "questions": []}
    unsolved = []
    global_question_id = [1]  # Mutable counter reference
    total_questions_extracted = 0
    completed_chunks = 0

    # Send initial progress
    yield {"type": "progress", "message": f"Đã chuẩn bị xong {len(chunks)} phần văn bản. Bắt đầu gửi cho AI..."}

    try:
        for completed_task in asyncio.as_completed(tasks):
            chunk_idx, chunk_data = await completed_task
            completed_chunks += 1
            yield {"type": "progress", "message": f"Đã xử lý xong {completed_chunks}/{len(chunks)} phần..."}

            if not chunk_data:
                continue

            if chunk_data.get("title") and merged_quiz["title"] == "Untitled Quiz":
                merged_quiz["title"] = chunk_data.get("title")

            chunk_questions = _normalize_questions(
                chunk_data, image_mapping or {}, prescan_keys, unsolved, global_question_id
            )
            merged_quiz["questions"].extend(chunk_questions)
            total_questions_extracted += len(chunk_questions)

            if chunk_questions:
                yield {"type": "chunk", "questions": chunk_questions}
    finally:
        for t in tasks:
            if not t.done():
                t.cancel()

    # Vision fallback when text extraction yields 0 questions
    if total_questions_extracted == 0 and file is not None:
        if settings.LM_STUDIO_API_BASE:
            yield {"type": "progress", "message": "Lỗi: Không tìm thấy câu hỏi nào! (Local Model không hỗ trợ đọc ảnh)"}
            logger.warning("Text extraction failed. Skipping Vision Fallback for Local LM.")
            yield {
                "type": "done",
                "title": "Không tìm thấy câu hỏi",
                "quiz_data": merged_quiz,
                "unsolved": []
            }
            return

        yield {"type": "progress", "message": "Bóc tách văn bản lỗi, tự động chuyển sang chế độ AI nhận diện hình ảnh..."}
        logger.warning("Text extraction failed (0 questions). Automatically triggering Vision Fallback streaming!")
        from app.services.pdf_extractor import extract_images_from_pdf
        image_chunks = await extract_images_from_pdf(file)

        instruction = """
You are a data extraction tool from exam photos.
Look at the following images and extract multiple-choice questions.
IMPORTANT NOTES:
- You MUST output ONLY valid JSON.
- For Mathematical formulas, wrap them in `$$` (e.g., `$$\\\\frac{1}{2}$$`).
- DO NOT solve the test. Do not output the correct answer or explanation.
- VERY IMPORTANT: Do NOT write long reasoning blocks. Output ONLY the JSON array.
"""

        async def process_image_chunk(chunk_idx, images):
            async with sem:
                try:
                    message_content = [{"type": "text", "text": instruction}]
                    for img_b64 in images:
                        message_content.append({
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{img_b64}"}
                        })
                    msg = HumanMessage(content=message_content)
                    llm_with_structure = llm.bind(response_format={"type": "json_schema", "json_schema": QUIZ_EXTRACTION_SCHEMA})
                    res = await llm_with_structure.ainvoke([msg])
                    logger.warning(f"RAW VISION LLM OUTPUT (Chunk {chunk_idx}):\n{res.content}\n---")

                    parsed_json = parse_json_from_text(res.content)
                    if isinstance(parsed_json, list):
                        return chunk_idx, {"title": "Untitled Quiz", "questions": parsed_json}
                    elif isinstance(parsed_json, dict) and "questions" in parsed_json:
                        return chunk_idx, parsed_json
                    else:
                        return chunk_idx, {"title": "Untitled Quiz", "questions": []}
                except Exception as e:
                    logger.error(f"Error processing vision chunk {chunk_idx}: {e}")
                    return chunk_idx, {}

        vision_tasks = [asyncio.create_task(process_image_chunk(i, imgs)) for i, imgs in enumerate(image_chunks)]

        vision_completed = 0
        for completed_task in asyncio.as_completed(vision_tasks):
            chunk_idx, chunk_data = await completed_task
            vision_completed += 1
            yield {"type": "progress", "message": f"Đã nhận diện xong {vision_completed}/{len(image_chunks)} phần hình ảnh..."}

            if not chunk_data:
                continue

            if chunk_data.get("title") and merged_quiz["title"] == "Untitled Quiz":
                merged_quiz["title"] = chunk_data.get("title")

            chunk_questions = _normalize_questions(
                chunk_data, image_mapping or {}, prescan_keys, unsolved, global_question_id
            )
            merged_quiz["questions"].extend(chunk_questions)

            if chunk_questions:
                yield {"type": "chunk", "questions": chunk_questions}

    yield {"type": "progress", "message": "Hoàn tất bóc tách!"}

    yield {
        "type": "done",
        "title": merged_quiz["title"],
        "quiz_data": merged_quiz,
        "unsolved": unsolved
    }
