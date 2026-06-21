import json
import logging
import asyncio
from typing import List, Dict, Any, Tuple
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
    content = content.strip()
    
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        logger.warning(f"Lỗi parse JSON gốc: {e}. Thử tự động fix escape LaTeX backslash...")
        fixed_content = content.replace('\\', '\\\\')
        fixed_content = fixed_content.replace('\\\\"', '\\"') # Khôi phục ngoặc kép
        fixed_content = fixed_content.replace('\\\\n', '\\n') # Khôi phục newline
        try:
            return json.loads(fixed_content)
        except json.JSONDecodeError as e2:
            logger.error(f"Fallback JSON parsing cũng thất bại: {e2}")
            # Trả về dict rỗng để kích hoạt fallback Vision
            return {}

async def _extract_quiz_structure(chunks: List[str], prescan_keys: dict = None) -> dict:
    """Bước 1: Sử dụng Flash để bóc tách sườn JSON song song từ văn bản."""
    logger.info(f"Bước 1: Bóc tách cấu trúc song song bằng gemini-1.5-flash với {len(chunks)} chunk(s)...")
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash", 
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0.1,
        max_retries=6,
        timeout=120,
    )
    
    prompt = PromptTemplate(
        input_variables=["text"],
        template_format="jinja2",
        template="""
Bạn là một công cụ trích xuất dữ liệu. Hãy đọc đoạn văn bản tài liệu sau và trích xuất thành danh sách câu hỏi trắc nghiệm (Quiz).
LƯU Ý QUAN TRỌNG: 
- Đối với công thức Toán học, BẮT BUỘC bao bọc bằng ký hiệu `$$` (ví dụ: `$$\\frac{1}{2}$$` hoặc `$$x^2$$`).
- BẮT BUỘC ESCAPE dấu gạch chéo ngược (`\`) thành (`\\`) trong JSON (ví dụ `\\\\frac`, `\\\\lim`, `\\\\sqrt`).
- Nếu có một đoạn thông tin/đoạn văn dùng chung cho nhiều câu hỏi (ví dụ: 'Dùng dữ kiện sau trả lời câu 1 đến 3'), BẮT BUỘC phải điền đoạn thông tin chung đó vào trường `shared_context` của TỪNG câu hỏi liên quan.
- KHÔNG TỰ GIẢI ĐỀ. Nếu trong tài liệu KHÔNG GHI SẴN ĐÁP ÁN, hãy để `correct_answer_id` và `explanation` là null.

Cấu trúc JSON mong đợi:
{
    "title": "Tên bài kiểm tra (nếu có ở đoạn này, nếu không thì để null)",
    "questions": [
        {
            "id": "1",
            "content": "Nội dung câu hỏi?",
            "shared_context": "Đoạn văn dùng chung (nếu có, mặc định null)",
            "image_base64": null,
            "answers": [
                {"id": "A", "content": "Đáp án 1"},
                {"id": "B", "content": "Đáp án 2"},
                {"id": "C", "content": "Đáp án 3"},
                {"id": "D", "content": "Đáp án 4"}
            ],
            "correct_answer_id": "A",
            "explanation": "Lời giải trong đề"
        }
    ]
}
        
Văn bản tài liệu:
{{ text }}
"""
    )
    
    chain = prompt | llm
    sem = asyncio.Semaphore(2) # Limit to 2 concurrent requests
    
    async def process_text_chunk(chunk_idx, text):
        async with sem:
            # Add delay to avoid 15 RPM rate limit (Gemini Free Tier)
            if chunk_idx > 0:
                await asyncio.sleep(4.0)
            
            # Custom retry logic for 429 ResourceExhausted
            for attempt in range(3):
                try:
                    res = await chain.ainvoke({"text": text})
                    return chunk_idx, _parse_json_from_text(res.content)
                except Exception as e:
                    if "429" in str(e) or "ResourceExhausted" in str(e):
                        logger.warning(f"Rate limit hit on chunk {chunk_idx}. Waiting 15s before retry...")
                        await asyncio.sleep(15.0)
                    else:
                        raise e
            return chunk_idx, {}

    tasks = [process_text_chunk(i, chunk) for i, chunk in enumerate(chunks)]
    results = await asyncio.gather(*tasks)
    
    # Sort by index to maintain document order
    sorted_results = sorted(results, key=lambda x: x[0])
    responses = [r[1] for r in sorted_results]
    
    merged_quiz = {
        "title": "Chưa có tên bài kiểm tra",
        "questions": []
    }
    
    global_answer_keys = prescan_keys or {}
    
    for response in responses:
        try:
            chunk_data = _parse_json_from_text(response.content)
            if not chunk_data:
                continue # Bỏ qua chunk bị lỗi JSON hoàn toàn
                
            if chunk_data.get("title") and merged_quiz["title"] == "Chưa có tên bài kiểm tra":
                merged_quiz["title"] = chunk_data.get("title")
                
            if chunk_data.get("answer_keys"):
                global_answer_keys.update(chunk_data["answer_keys"])
                
            for q in chunk_data.get("questions", []):
                # Filter bad AI data
                if not q.get("content"):
                    continue
                valid_answers = [a for a in q.get("answers", []) if a.get("id") and a.get("content")]
                if not valid_answers:
                    continue
                q["answers"] = valid_answers
                q["content"] = str(q["content"])
                q["original_id"] = str(q.get("id", ""))
                q["shared_context"] = q.get("shared_context")
                q["image_base64"] = q.get("image_base64")
                
                merged_quiz["questions"].append(q)
        except Exception as e:
            logger.error(f"Lỗi khi xử lý JSON chunk: {e}")
            
    # Gắn đáp án từ bảng đáp án (nếu có)
    global_question_id = 1
    for q in merged_quiz["questions"]:
        if not q.get("correct_answer_id"):
            ans_from_key = global_answer_keys.get(q.get("original_id")) or global_answer_keys.get(str(global_question_id))
            if ans_from_key:
                q["correct_answer_id"] = ans_from_key
                
        q["id"] = str(global_question_id)
        if "original_id" in q:
            del q["original_id"]
        global_question_id += 1
            
    return merged_quiz

async def _extract_quiz_structure_vision(image_chunks: List[List[str]]) -> dict:
    """Sử dụng Gemini Multimodal Vision để đọc ảnh chụp PDF."""
    logger.info(f"Bắt đầu Fallback Vision: Đọc {len(image_chunks)} cụm ảnh PDF bằng gemini-1.5-flash...")
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash", 
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0.1,
    )
    
    from langchain_core.messages import HumanMessage
    
    merged_quiz = {
        "title": "Chưa có tên bài kiểm tra",
        "questions": []
    }
    
    global_answer_keys = {}
    
    instruction = """
Bạn là một công cụ trích xuất dữ liệu Toán học/Vật lý từ ảnh chụp đề thi.
Hãy nhìn vào các bức ảnh sau, trích xuất thành danh sách câu hỏi trắc nghiệm (Quiz).
LƯU Ý QUAN TRỌNG VỀ TOÁN HỌC: 
- Đối với công thức Toán (phân số, tích phân, lim, căn, v.v.), hãy chuyển thành dạng LaTeX và BẮT BUỘC bao bọc bằng ký hiệu `$$` (ví dụ: `$$\\frac{1}{2}$$` hoặc `$$x^2$$`).
- BẮT BUỘC ESCAPE dấu gạch chéo ngược (`\`) thành (`\\`) trong JSON (ví dụ `\\\\frac`, `\\\\lim`, `\\\\sqrt`). 
- Nếu có một đoạn thông tin/đoạn văn dùng chung cho nhiều câu hỏi, BẮT BUỘC điền vào trường `shared_context` của từng câu hỏi liên quan.
- KHÔNG TỰ GIẢI ĐỀ. Để `correct_answer_id` và `explanation` là null nếu không có đáp án in sẵn.

Cấu trúc JSON mong đợi:
{
    "title": "Tên bài kiểm tra (nếu có ở đoạn này, nếu không thì để null)",
    "questions": [
        {
            "id": "1",
            "content": "Nội dung câu hỏi?",
            "shared_context": "Đoạn văn dùng chung (nếu có, mặc định null)",
            "image_base64": null,
            "answers": [
                {"id": "A", "content": "Đáp án 1"},
                {"id": "B", "content": "Đáp án 2"},
                {"id": "C", "content": "Đáp án 3"},
                {"id": "D", "content": "Đáp án 4"}
            ],
            "correct_answer_id": "A",
            "explanation": "Lời giải trong đề"
        }
    ],
    "answer_keys": {"1": "A", "2": "C"} // CHỈ SỬ DỤNG trường này nếu văn bản là bảng đáp án rời ở cuối đề. Key là số thứ tự câu hỏi, Value là đáp án đúng.
}
"""

    async def _process_image_chunk(images: List[str]):
        message_content = [{"type": "text", "text": instruction}]
        for img_b64 in images:
            message_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{img_b64}"}
            })
        msg = HumanMessage(content=message_content)
        return await llm.ainvoke([msg])

    tasks = [_process_image_chunk(chunk) for chunk in image_chunks]
    responses = await asyncio.gather(*tasks)
    
    for response in responses:
        try:
            chunk_data = _parse_json_from_text(response.content)
            if not chunk_data:
                continue
                
            if chunk_data.get("title") and merged_quiz["title"] == "Chưa có tên bài kiểm tra":
                merged_quiz["title"] = chunk_data.get("title")
                
            if chunk_data.get("answer_keys"):
                global_answer_keys.update(chunk_data["answer_keys"])
                
            for q in chunk_data.get("questions", []):
                # Filter bad AI data
                if not q.get("content"):
                    continue
                valid_answers = [a for a in q.get("answers", []) if a.get("id") and a.get("content")]
                if not valid_answers:
                    continue
                q["answers"] = valid_answers
                q["content"] = str(q["content"])
                q["original_id"] = str(q.get("id", ""))
                q["shared_context"] = q.get("shared_context")
                q["image_base64"] = q.get("image_base64")
                
                merged_quiz["questions"].append(q)
        except Exception as e:
            logger.error(f"Lỗi khi xử lý JSON Vision chunk: {e}")
            
    global_question_id = 1
    for q in merged_quiz["questions"]:
        if not q.get("correct_answer_id"):
            ans_from_key = global_answer_keys.get(q.get("original_id")) or global_answer_keys.get(str(global_question_id))
            if ans_from_key:
                q["correct_answer_id"] = ans_from_key
                
        q["id"] = str(global_question_id)
        if "original_id" in q:
            del q["original_id"]
        global_question_id += 1
            
    return merged_quiz


async def solve_quiz_questions(unsolved_questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Giải một danh sách các câu hỏi chưa có đáp án bằng Pro."""
    if not unsolved_questions:
        return []
        
    logger.info(f"Giải {len(unsolved_questions)} câu hỏi bằng gemini-1.5-flash...")
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash", 
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0.2,
        max_retries=6,
        timeout=120,
    )
    
    prompt = PromptTemplate(
        input_variables=["questions_json"],
        template_format="jinja2",
        template="""
Bạn là một giáo viên xuất sắc. Dưới đây là danh sách các câu hỏi trắc nghiệm chưa có đáp án.
Hãy giải từng câu, tìm ra đáp án đúng và viết lời giải thích ngắn gọn, dễ hiểu.

Input JSON:
{{ questions_json }}

Hãy trả về CHỈ MỘT MẢNG JSON hợp lệ chứa kết quả, tuyệt đối không có văn bản nào khác.
Cấu trúc JSON đầu ra mong đợi:
[
    {
        "id": "1",
        "correct_answer_id": "B",
        "explanation": "Vì theo định luật..."
    }
]
"""
    )
    
    chain = prompt | llm
    input_json = json.dumps(unsolved_questions, ensure_ascii=False)
    response = await chain.ainvoke({"questions_json": input_json})
    return _parse_json_from_text(response.content)

async def resolve_single_question(question_content: str, answers: list, old_answer_id: str, old_explanation: str) -> dict:
    """Giải lại 1 câu hỏi theo yêu cầu của học sinh (Re-solve)."""
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash", 
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0.4, # Nhiệt độ cao hơn để tư duy lại linh hoạt hơn
        max_retries=6,
        timeout=120,
    )
    
    prompt = PromptTemplate(
        input_variables=["q_content", "q_answers", "old_ans", "old_exp"],
        template_format="jinja2",
        template="""
Học sinh báo cáo rằng câu hỏi sau đây AI giải "cấn cấn" và có thể bị sai.
Bạn hãy đóng vai trò là một Gia sư siêu cấp, cực kỳ cẩn thận kiểm tra lại TỪNG BƯỚC MỘT (Step-by-step).

[CÂU HỎI]:
{{ q_content }}

[CÁC ĐÁP ÁN]:
{{ q_answers }}

[LỜI GIẢI CŨ BỊ HỌC SINH REPORT]:
- Đáp án cũ AI chọn: {{ old_ans }}
- Giải thích cũ: {{ old_exp }}

Hãy suy luận lại thật chính xác. Cuối cùng trả về JSON duy nhất:
{
    "correct_answer_id": "A",
    "explanation": "Lời giải thích mới chi tiết, logic và thuyết phục hơn, chỉ ra chỗ sai của lời giải cũ (nếu có)..."
}
"""
    )
    chain = prompt | llm
    response = await chain.ainvoke({
        "q_content": question_content,
        "q_answers": json.dumps(answers, ensure_ascii=False),
        "old_ans": old_answer_id,
        "old_exp": old_explanation
    })
    return _parse_json_from_text(response.content)

async def _prescan_answer_keys(text: str) -> dict:
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=settings.GEMINI_API_KEY, temperature=0.1, max_retries=6, timeout=120)
    prompt = PromptTemplate(
        input_variables=["text"],
        template_format="jinja2",
        template="""
Tìm bảng đáp án (Answer Key) trong đoạn văn bản cuối đề thi sau đây.
Trả về JSON duy nhất: {"answer_keys": {"1": "A", "2": "C"}}
Nếu không tìm thấy bất kỳ đáp án nào, trả về: {"answer_keys": {}}
Văn bản: {{ text }}
"""
    )
    res = await (prompt | llm).ainvoke({"text": text})
    parsed = _parse_json_from_text(res.content)
    return parsed.get("answer_keys", {}) if parsed else {}

async def _map_images_to_questions(quiz_data: dict, file) -> dict:
    from app.services.pdf_extractor import extract_images_from_pdf
    # Chỉ lấy chunk ảnh đầu tiên (giả sử có ít ảnh) hoặc gộp lại
    image_chunks = await extract_images_from_pdf(file, pages_per_chunk=50)
    if not image_chunks or not image_chunks[0]:
        return quiz_data
        
    all_images_b64 = image_chunks[0]
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=settings.GEMINI_API_KEY, temperature=0.1, max_retries=6, timeout=120)
    
    instruction = f"""
Dưới đây là một số bức ảnh được trích xuất từ đề thi và danh sách các câu hỏi (dạng JSON).
Nhiệm vụ của bạn là ghép cặp: Mỗi bức ảnh (đánh số từ 0 đến {len(all_images_b64)-1}) thuộc về câu hỏi nào?
Trả về một dictionary JSON đơn giản: key là ID câu hỏi, value là số thứ tự của bức ảnh (chỉ lấy bức ảnh quan trọng nhất cho mỗi câu).
Ví dụ: {{"1": 0, "5": 1}}
Nếu ảnh không thuộc câu nào hoặc không rõ, hãy bỏ qua.
JSON Câu hỏi:
{json.dumps([{"id": q["id"], "content": q["content"][:100]} for q in quiz_data["questions"]], ensure_ascii=False)}
"""
    from langchain_core.messages import HumanMessage
    message_content = [{"type": "text", "text": instruction}]
    for i, img_b64 in enumerate(all_images_b64):
        message_content.append({"type": "text", "text": f"Ảnh số {i}:"})
        message_content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{img_b64}"}
        })
        
    res = await llm.ainvoke([HumanMessage(content=message_content)])
    parsed = _parse_json_from_text(res.content)
    if parsed:
        for q in quiz_data["questions"]:
            qid = str(q["id"])
            if qid in parsed:
                img_idx = int(parsed[qid])
                if 0 <= img_idx < len(all_images_b64):
                    q["image_base64"] = all_images_b64[img_idx]
    return quiz_data

async def generate_quiz_from_text(chunks: List[str], file=None) -> Tuple[Quiz, List[Dict[str, Any]]]:
    """
    Hệ thống AI 2 Bước (Lazy Loading) kèm FALLBACK VISION:
    - Thử trích xuất bằng Text trước.
    - Nếu thất bại (0 câu hỏi), tự động Fallback sang Vision bằng cách đọc file gốc.
    """
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY chưa được cấu hình!")
        
    try:
        prescan_keys = {}
        if chunks:
            prescan_keys = await _prescan_answer_keys(chunks[-1])
            if prescan_keys:
                logger.info(f"Pre-scan tìm thấy {len(prescan_keys)} đáp án.")
                
        quiz_data = await _extract_quiz_structure(chunks, prescan_keys)
        
        # Kiểm tra Fallback
        if not quiz_data.get("questions") and file is not None:
            logger.warning("Trích xuất Text thất bại (0 câu hỏi). Tự động kích hoạt Fallback Vision!")
            from app.services.pdf_extractor import extract_images_from_pdf
            image_chunks = await extract_images_from_pdf(file)
            quiz_data = await _extract_quiz_structure_vision(image_chunks)
        elif file is not None:
            # Map images cho chế độ text (hybrid)
            quiz_data = await _map_images_to_questions(quiz_data, file)
        
        unsolved = []
        for q in quiz_data.get("questions", []):
            if not q.get("correct_answer_id"):
                unsolved.append({
                    "id": q.get("id"),
                    "content": q.get("content"),
                    "answers": q.get("answers")
                })
                
        # Lấy 2 câu đầu để giải ngay lập tức (Synchronous)
        sync_batch = unsolved[:2]
        remaining_unsolved = unsolved[2:]
        
        if sync_batch:
            solved_results = await solve_quiz_questions(sync_batch)
            solved_map = {str(item["id"]): item for item in solved_results}
            for q in quiz_data["questions"]:
                sid = str(q.get("id"))
                if sid in solved_map:
                    q["correct_answer_id"] = solved_map[sid].get("correct_answer_id")
                    q["explanation"] = solved_map[sid].get("explanation")
                    
        return Quiz(**quiz_data), remaining_unsolved
        
    except Exception as e:
        logger.error(f"Lỗi trong quá trình tạo Quiz: {e}")
        raise ValueError(f"Không thể xử lý văn bản thành Quiz: {e}")
from typing import AsyncGenerator
import asyncio
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings
from langchain_core.messages import HumanMessage

async def stream_quiz_from_pdf(chunks: list[str], file=None) -> AsyncGenerator[dict, None]:
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY chưa được cấu hình!")
        
    prescan_keys = {}
    if chunks:
        prescan_keys = await _prescan_answer_keys(chunks[-1])
        if prescan_keys:
            logger.info(f"Pre-scan tìm thấy {len(prescan_keys)} đáp án.")
            
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash", 
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0.1,
        max_retries=6,
        timeout=120,
    )
    
    prompt = PromptTemplate(
        input_variables=["text"],
        template_format="jinja2",
        template="""
Bạn là một công cụ trích xuất dữ liệu. Hãy đọc đoạn văn bản tài liệu sau và trích xuất thành danh sách câu hỏi trắc nghiệm (Quiz).
LƯU Ý QUAN TRỌNG: 
- Đối với công thức Toán học, BẮT BUỘC bao bọc bằng ký hiệu `$$` (ví dụ: `$$\\frac{1}{2}$$` hoặc `$$x^2$$`).
- BẮT BUỘC ESCAPE dấu gạch chéo ngược (`\\`) thành (`\\\\`) trong JSON (ví dụ `\\\\frac`, `\\\\lim`, `\\\\sqrt`).
- Nếu có một đoạn thông tin/đoạn văn dùng chung cho nhiều câu hỏi, BẮT BUỘC phải điền đoạn thông tin chung đó vào trường `shared_context` của TỪNG câu hỏi liên quan.
- KHÔNG TỰ GIẢI ĐỀ. Nếu trong tài liệu KHÔNG GHI SẴN ĐÁP ÁN, hãy để `correct_answer_id` và `explanation` là null.

Cấu trúc JSON mong đợi:
{
    "title": "Tên bài kiểm tra (nếu có ở đoạn này, nếu không thì để null)",
    "questions": [
        {
            "id": "1",
            "content": "Nội dung câu hỏi?",
            "shared_context": "Đoạn văn dùng chung (nếu có, mặc định null)",
            "image_base64": null,
            "answers": [
                {"id": "A", "content": "Đáp án 1"},
                {"id": "B", "content": "Đáp án 2"},
                {"id": "C", "content": "Đáp án 3"},
                {"id": "D", "content": "Đáp án 4"}
            ],
            "correct_answer_id": "A",
            "explanation": "Lời giải trong đề"
        }
    ]
}
        
Văn bản tài liệu:
{{ text }}
"""
    )
    
    chain = prompt | llm
    sem = asyncio.Semaphore(3)
    
    async def process_text_chunk(chunk_idx, text):
        async with sem:
            res = await chain.ainvoke({"text": text})
            return chunk_idx, _parse_json_from_text(res.content)
            
    tasks = [asyncio.create_task(process_text_chunk(i, text)) for i, text in enumerate(chunks)]
    
    merged_quiz = {"title": "Chưa có tên bài kiểm tra", "questions": []}
    unsolved = []
    global_question_id = 1
    total_questions_extracted = 0
    
    for completed_task in asyncio.as_completed(tasks):
        chunk_idx, chunk_data = await completed_task
        if not chunk_data:
            continue
            
        if chunk_data.get("title") and merged_quiz["title"] == "Chưa có tên bài kiểm tra":
            merged_quiz["title"] = chunk_data.get("title")
            
        chunk_questions = []
        for q in chunk_data.get("questions", []):
            if not q.get("content"): continue
            valid_answers = [a for a in q.get("answers", []) if a.get("id") and a.get("content")]
            if not valid_answers: continue
            
            q["answers"] = valid_answers
            q["content"] = str(q["content"])
            q["original_id"] = str(q.get("id", ""))
            q["id"] = str(global_question_id)
            
            ans = prescan_keys.get(q["original_id"]) or prescan_keys.get(str(global_question_id))
            if ans:
                q["correct_answer_id"] = ans
            else:
                unsolved.append(q)
                
            global_question_id += 1
            chunk_questions.append(q)
            merged_quiz["questions"].append(q)
            total_questions_extracted += 1
            
        if chunk_questions:
            yield {"type": "chunk", "questions": chunk_questions}
            
    if total_questions_extracted == 0 and file is not None:
        logger.warning("Trích xuất Text thất bại (0 câu hỏi). Tự động kích hoạt Fallback Vision streaming!")
        from app.services.pdf_extractor import extract_images_from_pdf
        image_chunks = await extract_images_from_pdf(file)
        
        instruction = """
Bạn là một công cụ trích xuất dữ liệu Toán học/Vật lý từ ảnh chụp đề thi.
Hãy nhìn vào các bức ảnh sau, trích xuất thành danh sách câu hỏi trắc nghiệm (Quiz).
LƯU Ý QUAN TRỌNG VỀ TOÁN HỌC: 
- Đối với công thức Toán (phân số, tích phân, lim, căn, v.v.), hãy chuyển thành dạng LaTeX và BẮT BUỘC bao bọc bằng ký hiệu `$$` (ví dụ: `$$\\frac{1}{2}$$` hoặc `$$x^2$$`).
- BẮT BUỘC ESCAPE dấu gạch chéo ngược (`\\`) thành (`\\\\`) trong JSON (ví dụ `\\\\frac`, `\\\\lim`, `\\\\sqrt`). 
- Nếu có một đoạn thông tin/đoạn văn dùng chung cho nhiều câu hỏi, BẮT BUỘC điền vào trường `shared_context` của từng câu hỏi liên quan.
- KHÔNG TỰ GIẢI ĐỀ. Để `correct_answer_id` và `explanation` là null nếu không có đáp án in sẵn.

Cấu trúc JSON mong đợi:
{
    "title": "Tên bài kiểm tra (nếu có ở đoạn này, nếu không thì để null)",
    "questions": [
        {
            "id": "1",
            "content": "Nội dung câu hỏi?",
            "shared_context": "Đoạn văn dùng chung (nếu có, mặc định null)",
            "image_base64": null,
            "answers": [
                {"id": "A", "content": "Đáp án 1"},
                {"id": "B", "content": "Đáp án 2"},
                {"id": "C", "content": "Đáp án 3"},
                {"id": "D", "content": "Đáp án 4"}
            ],
            "correct_answer_id": "A",
            "explanation": "Lời giải trong đề"
        }
    ],
    "answer_keys": {"1": "A", "2": "C"}
}
"""
        async def process_image_chunk(chunk_idx, images):
            async with sem:
                message_content = [{"type": "text", "text": instruction}]
                for img_b64 in images:
                    message_content.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{img_b64}"}
                    })
                msg = HumanMessage(content=message_content)
                res = await llm.ainvoke([msg])
                return chunk_idx, _parse_json_from_text(res.content)
                
        vision_tasks = [asyncio.create_task(process_image_chunk(i, imgs)) for i, imgs in enumerate(image_chunks)]
        
        for completed_task in asyncio.as_completed(vision_tasks):
            chunk_idx, chunk_data = await completed_task
            if not chunk_data:
                continue
                
            if chunk_data.get("title") and merged_quiz["title"] == "Chưa có tên bài kiểm tra":
                merged_quiz["title"] = chunk_data.get("title")
                
            chunk_questions = []
            if chunk_data.get("answer_keys"):
                prescan_keys.update(chunk_data["answer_keys"])
                
            for q in chunk_data.get("questions", []):
                if not q.get("content"): continue
                valid_answers = [a for a in q.get("answers", []) if a.get("id") and a.get("content")]
                if not valid_answers: continue
                
                q["answers"] = valid_answers
                q["content"] = str(q["content"])
                q["original_id"] = str(q.get("id", ""))
                q["id"] = str(global_question_id)
                
                ans = prescan_keys.get(q["original_id"]) or prescan_keys.get(str(global_question_id))
                if ans:
                    q["correct_answer_id"] = ans
                else:
                    unsolved.append(q)
                    
                global_question_id += 1
                chunk_questions.append(q)
                merged_quiz["questions"].append(q)
                
            if chunk_questions:
                yield {"type": "chunk", "questions": chunk_questions}

    elif total_questions_extracted > 0 and file is not None:
        merged_quiz = await _map_images_to_questions(merged_quiz, file)
        updates = [{"id": q["id"], "image_base64": q["image_base64"]} for q in merged_quiz["questions"] if q.get("image_base64")]
        if updates:
            yield {"type": "images_mapped", "updates": updates}

    # Final yield
    yield {
        "type": "done",
        "title": merged_quiz["title"],
        "quiz_data": merged_quiz,
        "unsolved": unsolved
    }
