from typing import Dict, Any

# In-memory database used as a fallback when MongoDB is unavailable
MOCK_QUIZ_DB: Dict[str, Any] = {}

def get_mock_quiz(quiz_id: str) -> Any:
    return MOCK_QUIZ_DB.get(quiz_id)

def set_mock_quiz(quiz_id: str, quiz_data: Any) -> None:
    MOCK_QUIZ_DB[quiz_id] = quiz_data
