import json
import re
import logging
from typing import Dict, Any, List, AsyncGenerator
import asyncio

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage
from app.schemas.quiz import Quiz, Question, Answer
from app.core.config import settings

logger = logging.getLogger(__name__)

def _get_llm(temperature: float = 0.1) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model="gemini-3.1-flash-lite", 
        google_api_key=settings.GEMINI_API_KEY,
        temperature=temperature,
        max_retries=6,
        timeout=120,
    )

def _parse_json_from_text(text: str) -> dict | list:
    """Extract and parse JSON from the AI's response text."""
    try:
        # Try direct parsing first
        return json.loads(text)
    except json.JSONDecodeError:
        pass
        
    # Regex to find JSON block
    match = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON block: {e}")
            return {}
    
    # Try finding the first { and last }
    start_idx = text.find('{')
    end_idx = text.rfind('}')
    
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        json_str = text[start_idx:end_idx+1]
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON substring: {e}")
            return {}
            
    logger.error("Could not find any valid JSON in the response.")
    return {}

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
    res = await (prompt | llm).ainvoke({"text": text})
    parsed = _parse_json_from_text(res.content)
    return parsed.get("answer_keys", {}) if parsed else {}

async def _map_images_to_questions(quiz_data: dict, file) -> dict:
    from app.services.pdf_extractor import extract_images_from_pdf
    image_chunks = await extract_images_from_pdf(file, pages_per_chunk=10)
    if not image_chunks:
        return quiz_data
        
    llm = _get_llm(temperature=0.1)
    
    questions_json = json.dumps([{"id": q["id"], "content": q["content"][:100]} for q in quiz_data["questions"]], ensure_ascii=False)
    
    global_image_idx = 0
    parsed_all = {}
    for chunk in image_chunks:
        if not chunk: continue
        instruction = f"""
Below are several images extracted from the exam and a list of questions (in JSON format).
Your task is to map each image (numbered from {global_image_idx} to {global_image_idx + len(chunk)-1}) to its corresponding question.
Return a simple JSON dictionary: key is the question ID, value is the image index (only keep the most important image for each question).
Example: {{"1": {global_image_idx}, "5": {global_image_idx + 1}}}
If an image does not belong to any question or is unclear, ignore it.
Questions JSON:
{questions_json}
"""
        message_content = [{"type": "text", "text": instruction}]
        for i, img_b64 in enumerate(chunk):
            message_content.append({"type": "text", "text": f"Image {global_image_idx + i}:"})
            message_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{img_b64}"}
            })
            
        res = await llm.ainvoke([HumanMessage(content=message_content)])
        parsed = _parse_json_from_text(res.content)
        if parsed and isinstance(parsed, dict):
            parsed_all.update(parsed)
            
        global_image_idx += len(chunk)
        
    all_images_b64 = [img for chunk in image_chunks for img in chunk]
    
    if parsed_all:
        for q in quiz_data["questions"]:
            qid = str(q["id"])
            if qid in parsed_all:
                img_idx = int(parsed_all[qid])
                if 0 <= img_idx < len(all_images_b64):
                    q["image_base64"] = all_images_b64[img_idx]
    return quiz_data

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

Return ONLY ONE valid JSON array containing the results. Do not output any other text.
Expected JSON output structure:
[
    {
        "id": "1",
        "correct_answer_id": "B",
        "explanation": "Because according to the law of..."
    }
]
"""
    )
    
    chain = prompt | llm
    input_json = json.dumps(unsolved_questions, ensure_ascii=False)
    response = await chain.ainvoke({"questions_json": input_json})
    result = _parse_json_from_text(response.content)
    if isinstance(result, dict):
        result = [result]
    return result if isinstance(result, list) else []

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

Think and solve it accurately again. Finally, return a single JSON:
{
    "correct_answer_id": "A",
    "explanation": "New detailed, logical, and convincing explanation, pointing out the mistake in the old solution (if any)..."
}
"""
    )
    chain = prompt | llm
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

async def stream_quiz_from_pdf(chunks: list[str], file=None) -> AsyncGenerator[dict, None]:
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not configured!")
        
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
You are a data extraction tool. Please read the following document text (converted to Markdown from PDF) and extract it into a list of multiple-choice questions (Quiz).
IMPORTANT NOTES: 
- For Mathematical formulas, you MUST wrap them in `$$` (e.g., `$$\\frac{1}{2}$$` or `$$x^2$$`).
- You MUST ESCAPE backslashes (`\\`) to (`\\\\`) in the JSON (e.g., `\\\\frac`, `\\\\lim`, `\\\\sqrt`).
- If there is a shared context/passage for multiple questions, you MUST fill that shared context into the `shared_context` field of EACH related question.
- DO NOT SOLVE THE TEST. If the document DOES NOT HAVE PRE-PRINTED ANSWERS, leave `correct_answer_id` and `explanation` as null.

Expected JSON structure:
{
    "title": "Test Title (if available in this section, else null)",
    "questions": [
        {
            "id": "1",
            "content": "Question content?",
            "shared_context": "Shared passage (if any, default null)",
            "image_base64": null,
            "answers": [
                {"id": "A", "content": "Answer 1"},
                {"id": "B", "content": "Answer 2"},
                {"id": "C", "content": "Answer 3"},
                {"id": "D", "content": "Answer 4"}
            ],
            "correct_answer_id": "A",
            "explanation": "Explanation in the test"
        }
    ]
}
        
Document text:
{{ text }}
"""
    )
    
    chain = prompt | llm
    sem = asyncio.Semaphore(3)
    
    async def process_text_chunk(chunk_idx, text):
        async with sem:
            try:
                res = await chain.ainvoke({"text": text})
                return chunk_idx, _parse_json_from_text(res.content)
            except Exception as e:
                logger.error(f"Error processing text chunk {chunk_idx}: {e}")
                return chunk_idx, {}
            
    tasks = [asyncio.create_task(process_text_chunk(i, text)) for i, text in enumerate(chunks)]
    
    merged_quiz = {"title": "Untitled Quiz", "questions": []}
    unsolved = []
    global_question_id = 1
    total_questions_extracted = 0
    
    try:
        for completed_task in asyncio.as_completed(tasks):
            chunk_idx, chunk_data = await completed_task
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
        logger.warning("Text extraction failed (0 questions). Automatically triggering Vision Fallback streaming!")
        from app.services.pdf_extractor import extract_images_from_pdf
        image_chunks = await extract_images_from_pdf(file)
        
        instruction = """
You are a Math/Physics data extraction tool from exam photos.
Look at the following images and extract them into a list of multiple-choice questions (Quiz).
IMPORTANT NOTES ON MATH: 
- For Math formulas (fractions, integrals, limits, roots, etc.), convert them to LaTeX format and MUST wrap them in `$$` (e.g., `$$\\frac{1}{2}$$` or `$$x^2$$`).
- MUST ESCAPE backslashes (`\\`) to (`\\\\`) in the JSON (e.g., `\\\\frac`, `\\\\lim`, `\\\\sqrt`). 
- If there is a shared context/passage for multiple questions, MUST fill it into the `shared_context` field of each related question.
- DO NOT SOLVE THE TEST. Leave `correct_answer_id` and `explanation` as null if there are no pre-printed answers.

Expected JSON structure:
{
    "title": "Test Title (if available in this section, else null)",
    "questions": [
        {
            "id": "1",
            "content": "Question content?",
            "shared_context": "Shared passage (if any, default null)",
            "image_base64": null,
            "answers": [
                {"id": "A", "content": "Answer 1"},
                {"id": "B", "content": "Answer 2"},
                {"id": "C", "content": "Answer 3"},
                {"id": "D", "content": "Answer 4"}
            ],
            "correct_answer_id": "A",
            "explanation": "Explanation in the test"
        }
    ],
    "answer_keys": {"1": "A", "2": "C"}
}
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
                    res = await llm.ainvoke([msg])
                    return chunk_idx, _parse_json_from_text(res.content)
                except Exception as e:
                    logger.error(f"Error processing vision chunk {chunk_idx}: {e}")
                    return chunk_idx, {}
                
        vision_tasks = [asyncio.create_task(process_image_chunk(i, imgs)) for i, imgs in enumerate(image_chunks)]
        
        for completed_task in asyncio.as_completed(vision_tasks):
            chunk_idx, chunk_data = await completed_task
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
