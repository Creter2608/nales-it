# Nales-It: Project State

## Current Architecture
- **Core Engine**: FastAPI backend that converts PDFs to Quizzes using LLM (OpenAI API spec, running via LM Studio or Gemini API).
- **Frontend**: Flutter + Riverpod, consuming SSE (Server-Sent Events) for real-time progressive UI updates.
- **Database**: MongoDB.

## Completed Tasks (Just Finished)
- **Resolved "Infinite Loading" loop**: Handled `asyncio.CancelledError` in `upload.py` to properly cancel background LM generation tasks when the client disconnects from the SSE stream, preventing LM Studio queue blockages.
- **Enabled Structured Output**: Refactored `quiz_generator.py` to entirely eliminate Regex (Markdown) parsing. The system now enforces strict JSON Schema (via `response_format={"type": "json_schema"}`) on all generation and reasoning steps.
- **Parser Robustness**: Upgraded parsing logic to use `json_repair` and robust JSON array slicing `[...]` to gracefully handle any stray `<think>` tags or markdown wrappers.

## Pending Tasks / Known Bugs
- Test new Structured Output stability with LM Studio local models in practice.
- Proceed to implement "Ngân hàng Câu hỏi" (Question Bank) to reuse parsing results and achieve 0-second load times.

## Running Services
- `cd backend` -> `uvicorn app.main:app --reload` (Port 8000)
- `cd mobile` -> `flutter run`
- LM Studio running local model on Port 1234.
