from pydantic import BaseModel
from pydantic import Field
from typing import List, Optional, Dict
from enum import Enum
from datetime import datetime


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)


class Character(BaseModel):
    id: str
    name: str
    description: str
    personality: str
    system_prompt: str
    avatar_url: str = "default_avatar.png"
    category: str = "general"
    tags: List[str] = []


class ConversationState(BaseModel):
    messages: List[Message] = Field(default_factory=list)
    last_activity: datetime = Field(default_factory=datetime.now)
    character_id: str
    user_id: str
    active: bool = True


class UserInput(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    character_id: Optional[str] = None
    user_id: str


class UserProfile(BaseModel):
    id: str
    username: str
    password_hash: str
    name: str = ""
    email: str = ""
    created_at: datetime = Field(default_factory=datetime.now)
    last_login: datetime = Field(default_factory=datetime.now)
    favorites: List[str] = []
