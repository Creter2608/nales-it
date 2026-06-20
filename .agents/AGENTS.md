# Nales-It Workspace Rules

This file defines the strict rules and tech stack decisions for the Nales-It project. Always follow these when working on this workspace.

## Technology Stack & Standards
- **Mobile App**: Flutter (Architecture: Feature-First / Clean Architecture. State Management: Riverpod/Bloc. Routing: GoRouter).
- **Backend**: Python (FastAPI). Dependency management via **Poetry**.
- **Database**: MongoDB.
- **AI Models**: Google Gemini or OpenAI GPT-4o-mini (optimized for JSON outputs).
- **DevOps**: Docker, Makefile, GitHub Actions for CI/CD, pre-commit hooks for code quality.

## AI Processing Pipeline (Crucial)
1. **No Raw Files to AI**: Do not feed raw large files (PDF, Word) directly to the AI model.
2. **Text Extraction**: Use Python libraries (PyMuPDF, python-docx) to extract text first.
3. **Chunking**: Use Regex/Logic to clean and chunk the text before sending to AI.
4. **Targeted AI Use**: Only use AI to process small text chunks and convert them into structured JSON Quiz format.
5. **Validation**: Validate AI output using Pydantic before saving to DB.
6. **Caching**: Implement file hash checking to avoid redundant AI calls.

## Professional Coding Standards
- **Documentation**: Write clear docstrings for core functions and use type hints (Python) / static typing (Dart).
- **Testing**: Write unit tests for core business logic in both backend (pytest) and mobile (flutter test).
- **Clean Code**: Adhere to SOLID principles. Separate business logic from UI/Controllers.

## Communication
- Always communicate with the user in Vietnamese.
