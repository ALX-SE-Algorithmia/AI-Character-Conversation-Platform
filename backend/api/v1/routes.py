from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.core.config import get_settings, Settings
from backend.service.container import get_platform

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    name: str
    version: str
    environment: str


class ChatRequest(BaseModel):
    character_id: str
    message: str
    user_id: str = "anonymous"
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    character_id: str
    conversation_id: str
    reply: str


@router.get("/health", response_model=HealthResponse)
def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
    )


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    platform = get_platform()
    result = platform.generate_response(
        message=req.message,
        conversation_id=req.conversation_id,
        character_id=req.character_id,
        user_id=req.user_id,
    )
    return ChatResponse(
        character_id=req.character_id,
        conversation_id=result["conversation_id"],
        reply=result["response"],
    )
