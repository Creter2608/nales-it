import os
import logging
from pathlib import Path
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.core.config import settings

logger = logging.getLogger(__name__)

class FabricAgent:
    def __init__(self, pattern_name: str, temperature: float = 0.1, model: str = None):
        self.pattern_name = pattern_name
        self.temperature = temperature
        self.model = model or settings.LM_STUDIO_MODEL
        self.system_prompt = self._load_pattern(pattern_name)
        
        # Add instruction to reply in Vietnamese but keep English code intact
        self.system_prompt += "\n\nCRITICAL INSTRUCTION: Please ensure your final output explanations are translated to Vietnamese, but keep code, commands, and technical terms in English."
        
        self.llm = ChatOpenAI(
            base_url=settings.LM_STUDIO_API_BASE,
            api_key=settings.LM_STUDIO_API_KEY,
            model=self.model,
            temperature=self.temperature,
            max_retries=3,
            timeout=120,
            max_tokens=4096,
        )

    def _load_pattern(self, pattern_name: str) -> str:
        pattern_file = Path(settings.FABRIC_PATTERNS_DIR) / pattern_name / "system.md"
        if not pattern_file.exists():
            raise FileNotFoundError(f"Fabric pattern '{pattern_name}' not found at {pattern_file}")
            
        with open(pattern_file, "r", encoding="utf-8") as f:
            return f.read()

    async def ainvoke(self, user_input: str) -> str:
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=user_input)
        ]
        response = await self.llm.ainvoke(messages)
        return response.content

    def invoke(self, user_input: str) -> str:
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=user_input)
        ]
        response = self.llm.invoke(messages)
        return response.content
