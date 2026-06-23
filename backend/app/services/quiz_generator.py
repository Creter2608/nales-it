import json
import re
import logging
from typing import Dict, Any, List, AsyncGenerator
import asyncio

from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage
from app.schemas.quiz import Quiz, Question, Answer
from app.core.config import settings

logger = logging.getLogger(__name__)

def _get_llm(temperature: float = 0.1) -> ChatOpenAI:
    return ChatOpenAI(
        base_url=settings.LM_STUDIO_API_BASE,
        api_key=settings.LM_STUDIO_API_KEY,
        model=settings.LM_STUDIO_MODEL,
        temperature=temperature,
        max_retries=6,
        timeout=600,
        max_tokens=8192,
    )

def _parse_json_from_text(text: str) -> dict | list:
    """Extract and parse JSON from the AI's response text."""
    import json_repair
    import re
    
    try:
        # Try direct parsing with repair
        parsed = json_repair.loads(text)
        if parsed is not None and isinstance(parsed, (dict, list)):
            return parsed
    except Exception:
        pass
        
    # Regex to find JSON block
    match = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL)
    if match:
        try:
            parsed = json_repair.loads(match.group(1))
            if parsed is not None and isinstance(parsed, (dict, list)):
                return parsed
        except Exception as e:
            logger.error(f"Error decoding JSON block: {e}")
    
    # Try finding the first { and last } or [ and ]
    first_brace = text.find('{')
    last_brace = text.rfind('}')
    first_bracket = text.find('[')
    last_bracket = text.rfind(']')
    
    # Check which one appears first (and is valid)
    start_idx = -1
    end_idx = -1
    
    if first_brace != -1 and (first_bracket == -1 or first_brace < first_bracket):
        start_idx = first_brace
        end_idx = last_brace
    elif first_bracket != -1:
        start_idx = first_bracket
        end_idx = last_bracket
        
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        json_str = text[start_idx:end_idx+1]
        try:
            parsed = json_repair.loads(json_str)
            if parsed is not None and isinstance(parsed, (dict, list)):
                return parsed
        except Exception as e:
            logger.error(f"Error decoding JSON substring: {e}")
            
    logger.error("Could not find any valid JSON in the response.")
    return {}

def _parse_markdown_to_quiz(text: str, image_mapping: dict = None) -> dict:
    """Parses standard markdown format into JSON questions format."""
    import re
    questions = []
    title = "Untitled Quiz"
    title_match = re.search(r'\[TITLE\]\s*(.*)', text, re.IGNORECASE)
    if title_match:
        title = title_match.group(1).strip()

    blocks = re.split(r'\[CAUHOI\]', text, flags=re.IGNORECASE)
    
    for block in blocks:
        block = block.strip()
        if not block or block.upper().startswith("UNTITLED QUIZ"): continue
            
        q_dict = {"content": "", "answers": [], "correct_answer_id": None, "explanation": None}
        
        # Find all DAPAN markers
        ans_matches = list(re.finditer(r'\[DAPAN_([A-Z])\]', block, re.IGNORECASE))
        if ans_matches:
            q_dict["content"] = block[:ans_matches[0].start()].strip()
            # Remove [TITLE] block from the first question's content if it leaked
            q_dict["content"] = re.sub(r'\[TITLE\].*', '', q_dict["content"], flags=re.IGNORECASE).strip()
            
            # Check for image tags
            q_dict["image_base64"] = None
            if image_mapping:
                for img_tag, b64 in image_mapping.items():
                    if img_tag in q_dict["content"]:
                        q_dict["image_base64"] = b64
                        # Remove tag from display text
                        q_dict["content"] = q_dict["content"].replace(img_tag, "").strip()
                        break
            
            for i, match in enumerate(ans_matches):
                ans_id = match.group(1).upper()
                start_pos = match.end()
                end_pos = ans_matches[i+1].start() if i + 1 < len(ans_matches) else len(block)
                ans_content = block[start_pos:end_pos].strip()
                q_dict["answers"].append({"id": ans_id, "content": ans_content})
        else:
            q_dict["content"] = block
            
        if q_dict["content"]:
            questions.append(q_dict)
            
    return {"title": title, "questions": questions}

async def _prescan_answer_keys(text: str) -> dict:
    llm = _get_llm(temperature=0.1)
    prompt = PromptTemplate(
        input_variables=["text"],
        template_format="jinja2",
        template="""
Find the Answer Key table in the following text (usually at the end of the exam).
Return a single JSON: {"answer_keys": {"1": "A", "2": "C"}}
If you cannot find any answer key, return: {"answer_keys": {}}
Text: {{ text }}
"""
    )
    
    schema = {
        "name": "answer_keys_extraction",
        "schema": {
            "type": "object",
            "properties": {
                "answer_keys": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "string"
                    }
                }
            },
            "required": ["answer_keys"],
            "additionalProperties": False
        },
        "strict": True
    }
    
    llm_structured = llm.bind(response_format={"type": "json_schema", "json_schema": schema})
    res = await (prompt | llm_structured).ainvoke({"text": text})
    parsed = _parse_json_from_text(res.content)
    return parsed.get("answer_keys", {}) if parsed else {}



async def solve_quiz_questions(unsolved_questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Solve a list of unsolved questions using Pro model."""
    if not unsolved_questions:
        return []
        
    logger.info(f"Solving {len(unsolved_questions)} questions using gemini-3.1-flash-lite...")
    llm = _get_llm(temperature=0.2)
    
    prompt = PromptTemplate(
        input_variables=["questions_json"],
        template_format="jinja2",
        template="""
You are an excellent teacher. Below is a list of multiple-choice questions without answers.
Please solve each question, find the correct answer, and write a short, easy-to-understand explanation.

Input JSON:
{{ questions_json }}

Return ONLY ONE valid JSON object containing the results. Do not output any other text.
"""
    )
    
    schema = {
        "name": "solve_questions",
        "schema": {
            "type": "object",
            "properties": {
                "results": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "correct_answer_id": {"type": "string"},
                            "explanation": {"type": "string"}
                        },
                        "required": ["id", "correct_answer_id", "explanation"],
                        "additionalProperties": False
                    }
                }
            },
            "required": ["results"],
            "additionalProperties": False
        },
        "strict": True
    }
    
    chain = prompt | llm.bind(response_format={"type": "json_schema", "json_schema": schema})
    input_json = json.dumps(unsolved_questions, ensure_ascii=False)
    
    try:
        response = await chain.ainvoke({"questions_json": input_json})
        results = _parse_json_from_text(response.content)
        if isinstance(results, dict) and "results" in results:
            results = results["results"]
        if not isinstance(results, list):
            results = []
    except Exception as e:
        logger.error(f"Error calling AI: {e}")
        results = []
    return results

async def resolve_single_question(question_content: str, answers: list, old_answer_id: str, old_explanation: str) -> dict:
    """Re-solve a single question requested by the student."""
    llm = _get_llm(temperature=0.4)
    
    prompt = PromptTemplate(
        input_variables=["q_content", "q_answers", "old_ans", "old_exp"],
        template_format="jinja2",
        template="""
The student reported that the previous AI's solution for the following question was questionable or incorrect.
Act as a Super Tutor and carefully re-evaluate the question STEP-BY-STEP.

[QUESTION]:
{{ q_content }}

[ANSWERS]:
{{ q_answers }}

[PREVIOUS SOLUTION REPORTED BY STUDENT]:
- Old selected answer: {{ old_ans }}
- Old explanation: {{ old_exp }}

Think and solve it accurately again. Finally, return ONLY ONE valid JSON object:
"""
    )
    
    schema = {
        "name": "resolve_question",
        "schema": {
            "type": "object",
            "properties": {
                "correct_answer_id": {"type": "string"},
                "explanation": {"type": "string"}
            },
            "required": ["correct_answer_id", "explanation"],
            "additionalProperties": False
        },
        "strict": True
    }
    
    chain = prompt | llm.bind(response_format={"type": "json_schema", "json_schema": schema})
    response = await chain.ainvoke({"q_content": question_content, "q_answers": json.dumps(answers, ensure_ascii=False), "old_ans": old_answer_id, "old_exp": old_explanation})
    result = _parse_json_from_text(response.content)
    return result if isinstance(result, dict) else {}

async def generate_feedback(score: int, total: int, wrong_questions: list) -> str:
    llm = _get_llm(temperature=0.7)
    prompt = PromptTemplate(
        input_variables=["score", "total", "wrong_list"],
        template="""
The student just finished the test and scored {score}/{total}.
List of questions the student answered incorrectly:
{wrong_list}

As a friendly AI tutor, write a short feedback paragraph (about 3-4 sentences) to:
1. Praise their effort.
2. Point out general weaknesses based on the incorrect answers (if any).
3. Encourage the student.
Do not explain each question in detail, just provide overall feedback.
"""
    )
    chain = prompt | llm
    wrong_list_str = "\n".join([f"- Question: {w['question']} | Chose incorrectly: {w['user_chose']} | Correct answer: {w['correct_was']}" for w in wrong_questions])
    if not wrong_list_str:
        wrong_list_str = "Student got 100% correct!"
        
    try:
        res = await chain.ainvoke({"score": score, "total": total, "wrong_list": wrong_list_str})
        return res.content
    except Exception as e:
        logger.error(f"Error calling AI for grading: {e}")
        return "AI is currently unavailable to provide feedback."

async def stream_quiz_from_pdf(chunks: list[str], image_mapping: dict = None, file=None) -> AsyncGenerator[dict, None]:
    """
    Process chunks concurrently and yield progress and partial results.
    """
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not configured!")
        
    yield {"type": "progress", "message": "Đang kiểm tra và quét bảng đáp án..."}
    prescan_keys = {}
    if chunks:
        prescan_keys = await _prescan_answer_keys(chunks[-1])
        if prescan_keys:
            logger.info(f"Pre-scan found {len(prescan_keys)} answers.")
            
    llm = _get_llm(temperature=0.1)
    
    prompt = PromptTemplate(
        input_variables=["text"],
        template_format="jinja2",
        template="""
You are a data extraction tool. Please read the following document text and extract multiple-choice questions.
IMPORTANT NOTES:
- You MUST output ONLY valid JSON.
- If you see an image placeholder like `[IMAGE_0]`, `[IMAGE_1]` in the text, you MUST include it inside the `content` of the question so we know which question it belongs to.
- For Mathematical formulas, wrap them in `$$` (e.g., `$$\\frac{1}{2}$$`).
- DO NOT solve the test. Do not output the correct answer or explanation.
- VERY IMPORTANT: Do NOT write long reasoning blocks. Output ONLY the JSON array.

Document text:
{{ text }}
"""
    )
    
    schema = {
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
    
    chain = prompt | llm.bind(response_format={"type": "json_schema", "json_schema": schema})
    sem = asyncio.Semaphore(3)
    
    async def process_text_chunk(chunk_idx, text):
        async with sem:
            try:
                res = await chain.ainvoke({"text": text})
                logger.warning(f"RAW LLM OUTPUT (Chunk {chunk_idx}):\n{res.content}\n---")
                
                parsed_json = _parse_json_from_text(res.content)
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
    global_question_id = 1
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
    finally:
        for t in tasks:
            if not t.done():
                t.cancel()
            
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
- For Mathematical formulas, wrap them in `$$` (e.g., `$$\\frac{1}{2}$$`).
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
                    llm_with_structure = llm.bind(response_format={"type": "json_schema", "json_schema": schema})
                    res = await llm_with_structure.ainvoke([msg])
                    logger.warning(f"RAW VISION LLM OUTPUT (Chunk {chunk_idx}):\n{res.content}\n---")
                    
                    parsed_json = _parse_json_from_text(res.content)
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

    yield {"type": "progress", "message": "Hoàn tất bóc tách!"}

    yield {
        "type": "done",
        "title": merged_quiz["title"],
        "quiz_data": merged_quiz,
        "unsolved": unsolved
    }
