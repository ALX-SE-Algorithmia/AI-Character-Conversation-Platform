from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import APIRouter, FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from backend.model.schemas import MessageRole, UserInput
from backend.service.container import get_platform


router = APIRouter()
platform = get_platform()

# Templates live in project-level `templates/`
templates = Jinja2Templates(directory="templates")


# HTML Endpoints


@router.post("/login")
async def login(request: Request):
    data = await request.json()
    username = data.get("username")
    password = data.get("password")
    user = platform.authenticate_user(username, password)
    if not user:
        user = platform.create_user(username, password)
    return RedirectResponse(url=f"/characters?user_id={user.id}", status_code=303)


@router.get("/characters", response_class=HTMLResponse)
async def characters_page(request: Request, user_id: str):
    characters = list(platform.characters_map.values())
    return templates.TemplateResponse(
        "characters.html", {"request": request, "characters": characters, "user_id": user_id}
    )


@router.get("/chat/{character_id}", response_class=HTMLResponse)
async def chat_page(request: Request, character_id: str, user_id: str, conversation_id: str | None = None):
    if character_id not in platform.characters_map:
        return RedirectResponse(url="/characters")
    character = platform.characters_map[character_id]
    if conversation_id and conversation_id in platform.conversations.conversations:
        conversation = platform.conversations.conversations[conversation_id]
        messages = [m for m in conversation.messages if m.role != MessageRole.SYSTEM]
    else:
        conversation_id = None
        messages = []
    return templates.TemplateResponse(
        "chat.html",
        {
            "request": request,
            "character": character,
            "user_id": user_id,
            "conversation_id": conversation_id,
            "messages": messages,
        },
    )


@router.get("/conversations", response_class=HTMLResponse)
async def conversations_page(request: Request, user_id: str):
    conversations = platform.get_user_conversations(user_id)
    return templates.TemplateResponse(
        "conversations.html", {"request": request, "conversations": conversations, "user_id": user_id}
    )


@router.get("/create-character", response_class=HTMLResponse)
async def create_character_page(request: Request, user_id: str):
    return templates.TemplateResponse("create_character.html", {"request": request, "user_id": user_id})


@router.post("/api/create-character")
async def api_create_character(request: Request):
    data = await request.json()
    topic = data.get("topic")
    traits = data.get("traits")
    user_id = data.get("user_id")
    traits_list = [trait.strip() for trait in traits.split(",") if trait.strip()]
    character = platform.generate_character(topic, traits_list)
    return RedirectResponse(url=f"/chat/{character.id}?user_id={user_id}", status_code=303)


@router.post("/api/send-message")
async def api_send_message(input: UserInput):
    result = platform.generate_response(
        input.message, input.conversation_id, input.character_id, input.user_id
    )
    return result


# WebSocket Endpoint
@router.websocket("/ws/chat/{user_id}/{character_id}/{conversation_id}")
async def websocket_chat(websocket: WebSocket, user_id: str, character_id: str, conversation_id: str | None = None):
    await websocket.accept()
    if conversation_id in ["null", "undefined"]:
        conversation_id = None
    if character_id not in platform.characters_map:
        await websocket.send_json({"error": f"Character with ID {character_id} not found"})
        await websocket.close()
        return
    character = platform.characters_map[character_id]
    await websocket.send_json(
        {
            "type": "welcome",
            "character": character.model_dump(),
            "message": f"Welcome to your conversation with {character.name}!",
        }
    )
    try:
        while True:
            message_text = await websocket.receive_text()
            if any(exit_phrase in message_text.lower() for exit_phrase in platform.exit_phrases):
                await websocket.send_json(
                    {
                        "type": "message",
                        "role": "assistant",
                        "content": "Goodbye! Let me know if you'd like to continue our conversation later.",
                        "timestamp": datetime.now().isoformat(),
                    }
                )
                break
            result = platform.generate_response(message_text, conversation_id, character_id, user_id)
            conversation_id = result["conversation_id"]
            await websocket.send_json(
                {
                    "type": "message",
                    "role": "assistant",
                    "content": result["response"],
                    "conversation_id": conversation_id,
                    "timestamp": datetime.now().isoformat(),
                }
            )
    except WebSocketDisconnect:
        platform.logger.info(f"WebSocket connection closed for conversation {conversation_id}")
    except Exception as e:
        platform.logger.error(f"Error in WebSocket: {str(e)}")
        await websocket.send_json({"type": "error", "message": "An error occurred during the conversation."})
