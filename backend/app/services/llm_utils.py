"""Shared LLM utilities for AI-powered quiz services."""

import json
import re
import logging
from langchain_openai import ChatOpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)


def get_llm(temperature: float = 0.1) -> ChatOpenAI:
    """Create a ChatOpenAI instance configured for LM Studio or compatible API."""
    return ChatOpenAI(
        base_url=settings.LM_STUDIO_API_BASE,
        api_key=settings.LM_STUDIO_API_KEY,
        model=settings.LM_STUDIO_MODEL,
        temperature=temperature,
        max_retries=6,
        timeout=600,
        max_tokens=8192,
    )


def parse_json_from_text(text: str) -> dict | list:
    """Extract and parse JSON from the AI's response text.

    Uses multiple fallback strategies:
    1. Direct parsing with json_repair
    2. Regex extraction from ```json``` code blocks
    3. Brace/bracket matching for embedded JSON
    """
    import json_repair

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


def parse_markdown_to_quiz(text: str, image_mapping: dict = None) -> dict:
    """Parses standard markdown format into JSON questions format."""
    questions = []
    title = "Untitled Quiz"
    title_match = re.search(r'\[TITLE\]\s*(.*)', text, re.IGNORECASE)
    if title_match:
        title = title_match.group(1).strip()

    blocks = re.split(r'\[CAUHOI\]', text, flags=re.IGNORECASE)

    for block in blocks:
        block = block.strip()
        if not block or block.upper().startswith("UNTITLED QUIZ"):
            continue

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
