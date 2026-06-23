"""Unit tests for core backend logic — schemas, llm_utils, config."""

import pytest
from unittest.mock import patch, AsyncMock

# ─── Schema Tests ───────────────────────────────────────────────

from app.schemas.quiz import Answer, Question, Quiz


class TestSchemas:
    """Test Pydantic schema validation."""

    def test_answer_valid(self):
        ans = Answer(id="A", content="Some answer")
        assert ans.id == "A"
        assert ans.content == "Some answer"

    def test_question_with_all_fields(self):
        q = Question(
            id="1",
            content="What is 2+2?",
            answers=[
                Answer(id="A", content="3"),
                Answer(id="B", content="4"),
            ],
            correct_answer_id="B",
            explanation="Basic arithmetic",
        )
        assert q.correct_answer_id == "B"
        assert len(q.answers) == 2

    def test_question_optional_fields(self):
        q = Question(
            id="1",
            content="Test",
            answers=[Answer(id="A", content="Ans")],
        )
        assert q.correct_answer_id is None
        assert q.explanation is None
        assert q.shared_context is None
        assert q.image_base64 is None

    def test_quiz_model(self):
        quiz = Quiz(
            title="Sample Quiz",
            questions=[
                Question(
                    id="1",
                    content="Q1",
                    answers=[Answer(id="A", content="A1")],
                )
            ],
        )
        assert quiz.title == "Sample Quiz"
        assert quiz.id is None
        assert len(quiz.questions) == 1

    def test_answer_missing_required_field(self):
        with pytest.raises(Exception):
            Answer(id="A")  # Missing content


# ─── LLM Utils Tests ───────────────────────────────────────────

from app.services.llm_utils import parse_json_from_text, parse_markdown_to_quiz


class TestParseJsonFromText:
    """Test JSON extraction from AI response text."""

    def test_direct_json(self):
        result = parse_json_from_text('{"key": "value"}')
        assert result == {"key": "value"}

    def test_json_in_code_block(self):
        text = '```json\n{"questions": [{"id": "1"}]}\n```'
        result = parse_json_from_text(text)
        assert result == {"questions": [{"id": "1"}]}

    def test_json_with_surrounding_text(self):
        text = 'Here is the result: {"answer": "B"} end of output.'
        result = parse_json_from_text(text)
        assert result == {"answer": "B"}

    def test_json_array(self):
        text = '[{"id": "1"}, {"id": "2"}]'
        result = parse_json_from_text(text)
        assert isinstance(result, list)
        assert len(result) == 2

    def test_no_json_returns_empty_dict(self):
        result = parse_json_from_text("No JSON here at all")
        assert result == {}

    def test_malformed_json_with_repair(self):
        # json_repair should handle minor issues like trailing commas
        text = '{"key": "value",}'
        result = parse_json_from_text(text)
        assert result.get("key") == "value"


class TestParseMarkdownToQuiz:
    """Test markdown quiz format parsing."""

    def test_basic_quiz(self):
        text = """[TITLE] Sample Test
[CAUHOI] What is 2+2?
[DAPAN_A] 3
[DAPAN_B] 4
[DAPAN_C] 5
[DAPAN_D] 6
"""
        result = parse_markdown_to_quiz(text)
        assert result["title"] == "Sample Test"
        # The title block before first [CAUHOI] is also parsed as a content-only entry
        questions_with_answers = [q for q in result["questions"] if q["answers"]]
        assert len(questions_with_answers) == 1
        assert len(questions_with_answers[0]["answers"]) == 4

    def test_no_title(self):
        text = """[CAUHOI] Question 1
[DAPAN_A] Answer A
[DAPAN_B] Answer B
"""
        result = parse_markdown_to_quiz(text)
        assert result["title"] == "Untitled Quiz"

    def test_empty_text(self):
        result = parse_markdown_to_quiz("")
        assert result["title"] == "Untitled Quiz"
        assert result["questions"] == []

    def test_image_mapping(self):
        text = """[CAUHOI] [IMAGE_0] What does this show?
[DAPAN_A] Option A
[DAPAN_B] Option B
"""
        mapping = {"[IMAGE_0]": "base64data=="}
        result = parse_markdown_to_quiz(text, image_mapping=mapping)
        q = result["questions"][0]
        assert q["image_base64"] == "base64data=="
        assert "[IMAGE_0]" not in q["content"]


# ─── Config Tests ───────────────────────────────────────────────

from app.core.config import Settings


class TestConfig:
    """Test configuration behavior."""

    def test_ai_enabled_with_lm_studio(self):
        s = Settings(LM_STUDIO_API_BASE="http://localhost:1234/v1", GEMINI_API_KEY="")
        assert s.ai_enabled is True

    def test_ai_enabled_with_gemini(self):
        s = Settings(LM_STUDIO_API_BASE="", GEMINI_API_KEY="some-key")
        assert s.ai_enabled is True

    def test_ai_disabled(self):
        s = Settings(LM_STUDIO_API_BASE="", GEMINI_API_KEY="")
        assert s.ai_enabled is False

    def test_default_cors(self):
        s = Settings()
        assert "*" not in s.ALLOWED_ORIGINS


# ─── Auth Tests ─────────────────────────────────────────────────

from app.core.auth import verify_api_key


class TestAuth:
    """Test API key authentication dependency."""

    @pytest.mark.asyncio
    async def test_dev_mode_no_key_required(self):
        with patch("app.core.auth.settings") as mock_settings:
            mock_settings.API_KEY = ""
            result = await verify_api_key(api_key=None)
            assert result == "dev-mode"

    @pytest.mark.asyncio
    async def test_valid_key(self):
        with patch("app.core.auth.settings") as mock_settings:
            mock_settings.API_KEY = "secret-123"
            result = await verify_api_key(api_key="secret-123")
            assert result == "secret-123"

    @pytest.mark.asyncio
    async def test_missing_key_raises_401(self):
        from fastapi import HTTPException
        with patch("app.core.auth.settings") as mock_settings:
            mock_settings.API_KEY = "secret-123"
            with pytest.raises(HTTPException) as exc_info:
                await verify_api_key(api_key=None)
            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_wrong_key_raises_403(self):
        from fastapi import HTTPException
        with patch("app.core.auth.settings") as mock_settings:
            mock_settings.API_KEY = "secret-123"
            with pytest.raises(HTTPException) as exc_info:
                await verify_api_key(api_key="wrong-key")
            assert exc_info.value.status_code == 403
