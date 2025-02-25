import os
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Ensure necessary directories exist before mounting static files and templates
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)

from main import ConversationPlatform, MessageRole, UserInput

# Initialize the conversation platform from the business logic module
platform = ConversationPlatform()

# Use a lifespan event handler instead of the deprecated on_event decorator
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: schedule background cleanup and attach logger
    asyncio.create_task(platform.cleanup_task())
    app.state.logger = platform.logger
    app.state.logger.info("Background cleanup task scheduled")
    yield
    # Shutdown events can be added here if needed

app = FastAPI(lifespan=lifespan, title="AI Character Conversation Platform")
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# ----- HTML Endpoints -----

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# Updated login endpoint to accept a JSON payload instead of form data
@app.post("/login")
async def login(request: Request):
    data = await request.json()
    username = data.get("username")
    password = data.get("password")
    user = platform.authenticate_user(username, password)
    if not user:
        user = platform.create_user(username, password)
    return RedirectResponse(url=f"/characters?user_id={user.id}", status_code=303)

@app.get("/characters", response_class=HTMLResponse)
async def characters_page(request: Request, user_id: str):
    characters = list(platform.characters.values())
    return templates.TemplateResponse("characters.html", {"request": request, "characters": characters, "user_id": user_id})

@app.get("/chat/{character_id}", response_class=HTMLResponse)
async def chat_page(request: Request, character_id: str, user_id: str, conversation_id: str = None):
    if character_id not in platform.characters:
        return RedirectResponse(url="/characters")
    character = platform.characters[character_id]
    if conversation_id and conversation_id in platform.conversation_storage:
        conversation = platform.conversation_storage[conversation_id]
        messages = [m for m in conversation.messages if m.role != MessageRole.SYSTEM]
    else:
        conversation_id = None
        messages = []
    return templates.TemplateResponse("chat.html", {
        "request": request,
        "character": character,
        "user_id": user_id,
        "conversation_id": conversation_id,
        "messages": messages
    })

@app.get("/conversations", response_class=HTMLResponse)
async def conversations_page(request: Request, user_id: str):
    conversations = platform.get_user_conversations(user_id)
    return templates.TemplateResponse("conversations.html", {"request": request, "conversations": conversations, "user_id": user_id})

@app.get("/create-character", response_class=HTMLResponse)
async def create_character_page(request: Request, user_id: str):
    return templates.TemplateResponse("create_character.html", {"request": request, "user_id": user_id})

# Updated create-character endpoint to accept JSON data instead of form data
@app.post("/api/create-character")
async def api_create_character(request: Request):
    data = await request.json()
    topic = data.get("topic")
    traits = data.get("traits")
    user_id = data.get("user_id")
    traits_list = [trait.strip() for trait in traits.split(",") if trait.strip()]
    character = platform.generate_character(topic, traits_list)
    return RedirectResponse(url=f"/chat/{character.id}?user_id={user_id}", status_code=303)

@app.post("/api/send-message")
async def api_send_message(input: UserInput):
    result = await platform.generate_response(input.message, input.conversation_id, input.character_id, input.user_id)
    return result

# ----- WebSocket Endpoint -----

@app.websocket("/ws/chat/{user_id}/{character_id}/{conversation_id}")
async def websocket_chat(websocket: WebSocket, user_id: str, character_id: str, conversation_id: str = None):
    await websocket.accept()
    if conversation_id in ["null", "undefined"]:
        conversation_id = None
    if character_id not in platform.characters:
        await websocket.send_json({"error": f"Character with ID {character_id} not found"})
        await websocket.close()
        return
    character = platform.characters[character_id]
    await websocket.send_json({
        "type": "welcome",
        "character": character.model_dump(),
        "message": f"Welcome to your conversation with {character.name}!"
    })
    try:
        while True:
            message_text = await websocket.receive_text()
            if any(exit_phrase in message_text.lower() for exit_phrase in platform.config.exit_phrases):
                await websocket.send_json({
                    "type": "message",
                    "role": "assistant",
                    "content": "Goodbye! Let me know if you'd like to continue our conversation later.",
                    "timestamp": datetime.now().isoformat()
                })
                break
            result = await platform.generate_response(message_text, conversation_id, character_id, user_id)
            conversation_id = result["conversation_id"]
            await websocket.send_json({
                "type": "message",
                "role": "assistant",
                "content": result["response"],
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat()
            })
    except WebSocketDisconnect:
        platform.logger.info(f"WebSocket connection closed for conversation {conversation_id}")
    except Exception as e:
        platform.logger.error(f"Error in WebSocket: {str(e)}")
        await websocket.send_json({
            "type": "error",
            "message": "An error occurred during the conversation."
        })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
