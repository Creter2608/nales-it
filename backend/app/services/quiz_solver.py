"""Quiz solving services — answer key scanning, batch solving, and single question resolution."""

import json
import logging
from typing import Dict, Any, List

from langchain_core.prompts import PromptTemplate
from app.services.llm_utils import get_llm, parse_json_from_text

logger = logging.getLogger(__name__)


async def prescan_answer_keys(text: str) -> dict:
    """Scan text for an existing answer key table and extract it."""
    llm = get_llm(temperature=0.1)
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
    parsed = parse_json_from_text(res.content)
    return parsed.get("answer_keys", {}) if parsed else {}


async def solve_quiz_questions(unsolved_questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Solve a list of unsolved questions using the configured LLM."""
    if not unsolved_questions:
        return []

    logger.info(f"Solving {len(unsolved_questions)} questions...")
    llm = get_llm(temperature=0.2)

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
        results = parse_json_from_text(response.content)
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
    llm = get_llm(temperature=0.4)

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
    response = await chain.ainvoke({
        "q_content": question_content,
        "q_answers": json.dumps(answers, ensure_ascii=False),
        "old_ans": old_answer_id,
        "old_exp": old_explanation,
    })
    result = parse_json_from_text(response.content)
    return result if isinstance(result, dict) else {}
