"""Quiz generator — backward-compatible facade.

This module re-exports all quiz-related functions from their new locations
so existing imports like `from app.services.quiz_generator import X` continue to work.

Internal modules:
- llm_utils: Shared LLM helpers (get_llm, parse_json_from_text)
- quiz_solver: Answer key scanning, batch solving, single question resolution
- quiz_grader: AI feedback generation
- quiz_extractor: PDF-to-quiz streaming pipeline
"""

# Re-export all public APIs for backward compatibility
from app.services.quiz_solver import (  # noqa: F401
    solve_quiz_questions,
    resolve_single_question,
)
from app.services.quiz_grader import generate_feedback  # noqa: F401
from app.services.quiz_extractor import stream_quiz_from_pdf  # noqa: F401
