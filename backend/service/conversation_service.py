from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from backend.core.logging import get_logger
from backend.model.schemas import ConversationState, Message, MessageRole


logger = get_logger(__name__)


class ConversationService:
    def __init__(self, data_dir: Path, inactivity_timeout_seconds: int = 1800):
        self.conversations_dir = data_dir / "conversations"
        self.conversations_dir.mkdir(parents=True, exist_ok=True)
        self.inactivity_timeout = timedelta(seconds=inactivity_timeout_seconds)
        self.conversations: Dict[str, ConversationState] = {}
        self._load_conversations()

    # Persistence
    def _load_conversations(self) -> None:
        try:
            loaded = 0
            for file_path in self.conversations_dir.glob("*.json"):
                try:
                    with open(file_path, "r") as f:
                        conversation_data = json.load(f)
                    # parse timestamps
                    for msg in conversation_data.get("messages", []):
                        if "timestamp" in msg:
                            msg["timestamp"] = datetime.fromisoformat(msg["timestamp"])
                    if "last_activity" in conversation_data:
                        conversation_data["last_activity"] = datetime.fromisoformat(conversation_data["last_activity"])
                    conv_id = file_path.stem
                    self.conversations[conv_id] = ConversationState(**conversation_data)
                    loaded += 1
                except Exception as e:
                    logger.error("Error loading conversation %s: %s", file_path, e)
            logger.info("Loaded %d conversations", loaded)
        except Exception as e:
            logger.error("Error loading conversations: %s", e)

    def save_conversation(self, conversation_id: str) -> None:
        if conversation_id not in self.conversations:
            return
        try:
            conv = self.conversations[conversation_id]
            conv_dict = conv.model_dump()
            for msg in conv_dict["messages"]:
                msg["timestamp"] = msg["timestamp"].isoformat()
            conv_dict["last_activity"] = conv_dict["last_activity"].isoformat()
            out_path = self.conversations_dir / f"{conversation_id}.json"
            with open(out_path, "w") as f:
                json.dump(conv_dict, f, indent=2)
        except Exception as e:
            logger.error("Error saving conversation %s: %s", conversation_id, e)

    # Ops
    def add_message(self, conversation_id: str, role: MessageRole, content: str) -> None:
        if conversation_id not in self.conversations:
            raise ValueError(f"Conversation {conversation_id} not found")
        conv = self.conversations[conversation_id]
        conv.messages.append(Message(role=role, content=content))
        conv.last_activity = datetime.now()

    def ensure_conversation(self, conversation_id: Optional[str], *, user_id: str, character_id: str) -> str:
        from uuid import uuid4
        if not conversation_id or conversation_id not in self.conversations:
            conversation_id = str(uuid4())
            self.conversations[conversation_id] = ConversationState(
                character_id=character_id,
                user_id=user_id,
            )
        return conversation_id

    def clean_inactive(self) -> None:
        now = datetime.now()
        for conv_id, conv in list(self.conversations.items()):
            if now - conv.last_activity > self.inactivity_timeout:
                conv.active = False
                logger.info("Conversation %s marked inactive", conv_id)

    def get_user_conversations(self, user_id: str) -> List[Dict[str, str]]:
        items = []
        for conv_id, conv in self.conversations.items():
            if conv.user_id == user_id:
                last_message = ""
                non_system = [m for m in conv.messages if m.role != MessageRole.SYSTEM]
                if non_system:
                    last_message = non_system[-1].content
                items.append({
                    "id": conv_id,
                    "character_id": conv.character_id,
                    "last_activity": conv.last_activity.isoformat(),
                    "message_count": len(non_system),
                    "preview": last_message[:100] + ("..." if len(last_message) > 100 else ""),
                })
        items.sort(key=lambda x: x["last_activity"], reverse=True)
        return items
