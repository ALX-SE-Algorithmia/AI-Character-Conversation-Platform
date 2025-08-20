from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from backend.core.config import Settings
from backend.core.logging import get_logger
from backend.model.schemas import (
    Character,
    ConversationState,
    MessageRole,
)
from backend.service.character_service import CharacterService
from backend.service.conversation_service import ConversationService
from backend.service.llm_service import LLMService
from backend.service.user_service import UserService


logger = get_logger(__name__)


class PlatformService:
    """
    High-level orchestrator mirroring the former ConversationPlatform responsibilities.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = get_logger(__name__)
        self.data_dir = Path("data")
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Subsystems
        self.llm = LLMService(settings)
        self.characters = CharacterService(self.data_dir, self.llm)
        self.conversations = ConversationService(self.data_dir, inactivity_timeout_seconds=1800)
        self.users = UserService()
        self.exit_phrases = {"thank you", "thanks", "bye", "goodbye", "exit", "stop"}

    # Character flows
    def generate_character(self, topic: str, traits: List[str]) -> Character:
        return self.characters.generate_character(topic, traits)

    # Conversation flows
    def _system_prompt_for(self, character: Character, is_first_message: bool) -> str:
        system_prompt = character.system_prompt
        if is_first_message:
            intro = (
                f"\n\nYou are {character.name}. {character.description}\n"
                f"Personality: {character.personality}\n\n"
                "This is the first message from the user. Introduce yourself briefly and then respond."
            )
            system_prompt = f"{system_prompt}{intro}"
        return system_prompt

    def generate_response(self, message: str, conversation_id: Optional[str], character_id: str, user_id: str) -> Dict[str, str]:
        if character_id not in self.characters.characters:
            raise ValueError(f"Character with ID {character_id} not found")
        character = self.characters.characters[character_id]

        # Ensure conversation
        conv_id = self.conversations.ensure_conversation(conversation_id, user_id=user_id, character_id=character_id)
        conv = self.conversations.conversations[conv_id]

        # Determine if first user message
        is_first = not any(m.role == MessageRole.USER for m in conv.messages)
        system_prompt = self._system_prompt_for(character, is_first)

        # Build LLM messages
        messages = [{"role": "system", "content": system_prompt}]
        for m in conv.messages:
            if m.role != MessageRole.SYSTEM:
                messages.append({"role": m.role.value, "content": m.content})
        messages.append({"role": "user", "content": message})

        # Call LLM
        text = self.llm.chat(messages, model="Llama3-8b-8192", temperature=0.7, max_tokens=1024)
        cleaned = self._clean_response(text)

        # Persist
        self.conversations.add_message(conv_id, MessageRole.USER, message)
        self.conversations.add_message(conv_id, MessageRole.ASSISTANT, cleaned)
        self.conversations.save_conversation(conv_id)

        return {"conversation_id": conv_id, "response": cleaned}

    @staticmethod
    def _clean_response(response: str) -> str:
        response = response.strip()
        prefixes = [
            "MessageRole.ASSISTANT:",
            "MessageRole.ASSISTANT",
            "Assistant:",
            "assistant:",
            "ASSISTANT:",
            "Response:",
            "Answer:",
        ]
        for p in prefixes:
            if response.startswith(p):
                return response[len(p):].strip()
        return response

    # User flows
    def create_user(self, username: str, password: str):
        return self.users.create_user(username, password)

    def authenticate_user(self, username: str, password: str):
        return self.users.authenticate(username, password)

    # Queries
    @property
    def characters_map(self):
        return self.characters.characters

    def get_user_conversations(self, user_id: str):
        return self.conversations.get_user_conversations(user_id)

    # Housekeeping
    def clean_inactive_conversations(self) -> None:
        self.conversations.clean_inactive()

    # Background loop (optional)
    async def cleanup_task(self):
        import asyncio
        while True:
            try:
                self.clean_inactive_conversations()
                await asyncio.sleep(300)
            except Exception as e:
                self.logger.error("Error in cleanup task: %s", e)
                await asyncio.sleep(60)
