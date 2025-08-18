from __future__ import annotations

from typing import List, Optional, Dict, Any
from backend.core.config import Settings
from backend.core.logging import get_logger


logger = get_logger(__name__)


class LLMService:
    """
    Wraps access to Groq / LangChain models. Falls back to a stub mode if
    no API key is provided, so development and tests can run offline.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.stub_mode = not bool(settings.GROQ_API_KEY)
        if self.stub_mode:
            logger.warning("LLMService running in STUB mode (GROQ_API_KEY not set)")
        else:
            try:
                from groq import Groq  # type: ignore
                from langchain_groq import ChatGroq  # type: ignore
                self._groq_client = Groq(api_key=settings.GROQ_API_KEY)
                # Default model; callers may override
                self._llm = ChatGroq(groq_api_key=settings.GROQ_API_KEY, model_name="Llama3-8b-8192")
            except Exception as e:
                logger.error("Failed to initialize Groq/ChatGroq: %s", e)
                self.stub_mode = True

    def chat(self, messages: List[Dict[str, str]], *, model: str = "Llama3-8b-8192",
             temperature: float = 0.7, max_tokens: int = 1024) -> str:
        if self.stub_mode:
            # Very simple echo for local dev/tests
            user_last = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
            return f"[stub] You said: {user_last}"
        try:
            completion = self._groq_client.chat.completions.create(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return completion.choices[0].message.content
        except Exception as e:
            logger.error("LLM chat error: %s", e)
            return "I'm having trouble responding right now."
