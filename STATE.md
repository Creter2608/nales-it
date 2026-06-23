# Nales-It Backend State

## Current Architecture
- **Framework**: FastAPI (Python 3.11+)
- **Database**: MongoDB (via Motor async) with a fallback to in-memory MockDB.
- **AI Integration**: LangChain connecting to either LM Studio (Local LLM - default google/gemma-4-e4b) or Gemini (cloud).
- **Core Features**: 
  - Upload PDF, extract text/images (PyMuPDF) -> AI processes to generate Multiple Choice Questions.
  - Streaming SSE to client during AI processing.
  - Background tasks for solving chunks of questions.
  - In-memory rate limiting and API Key authentication middleware.
- **Modules Breakdown (Refactored)**: `llm_utils.py`, `quiz_solver.py`, `quiz_grader.py`, `quiz_extractor.py` and a facade `quiz_generator.py`.

## Completed Tasks
- **Phase 1 (Critical Fixes)**: Fixed `obj_id` undefined NameError, missing imports (`random`, `string`) in `upload.py`, removed exposed `GEMINI_API_KEY` from `.env`, and fixed variable shadowing in the background chunk solver loop.
- **Phase 2 (Security Hardening)**: Restricted CORS default to `localhost:3000, localhost:8080`, unhardcoded `DATABASE_NAME` in `mongodb.py`, fixed gate logic mismatch with `ai_enabled` property, and introduced `API_KEY` based authentication middleware (`X-API-Key`).
- **Phase 3 (Architecture & Quality)**: Split the monolithic `quiz_generator.py` (549 lines) into 4 specialized modules with a backward-compatible facade. Cleaned up unused imports. Added 23 comprehensive Pytest unit tests. Implemented simple in-memory rate limiting (5 reqs/60s) for the `/api/v1/upload/pdf` endpoint.

## Pending Tasks / Known Bugs
- Add integration tests for the endpoints.
- Replace simple in-memory rate limiting with Redis if deploying horizontally (multiple workers).
- Wire up frontend to consume the `X-API-Key` securely in production.
- (Optional) Revoke the old Gemini API Key on Google AI Studio as it was previously leaked.

## Running Services
- **Backend API**: `poetry run uvicorn app.main:app --reload` (Runs on `http://localhost:8000`)
- **Tests**: `poetry run pytest tests/test_unit.py -v`
