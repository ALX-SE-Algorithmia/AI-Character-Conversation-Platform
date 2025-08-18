# AI Character Conversation Platform — Backend

A modular FastAPI backend for the AI Character Conversation Platform. Organized with clear layers: `api`, `core`, `service`, `model`, `utils`. Includes tests (pytest), packaging (pyproject, setup.py), demo client, and conda environment.

## Architecture

- **`backend/main.py`**: App factory and ASGI app. Includes `api.v1` and `web` routers, mounts `/static`, and schedules cleanup in a lifespan handler.
- **`backend/api/v1/routes.py`**: HTTP endpoints (`/health`, `/chat`).
- **`backend/web/routes.py`**: HTML pages and WebSocket routes (characters, chat, conversations, create-character, ws chat).
- **`backend/core/config.py`**: Pydantic `Settings` with `.env` support.
- **`backend/core/logging.py`**: Structured logging config and `get_logger()`.
- **`backend/service/chat_service.py`**: Business logic (currently stubbed).
- **`backend/model/schemas.py`**: Pydantic domain schemas.
- **`backend/utils/faiss_helper.py`**: Utility example.
- **`backend/tests/`**: Pytest suite covering health and chat stub.
- **`backend/api_demo.py`**: Minimal client using `requests`.

## Endpoints

API v1

- **GET `/api/v1/health`** → Returns service status and metadata.
- **POST `/api/v1/chat`** → Body: `{ character_id: string, message: string }`. Returns stubbed reply.

Web UI and Actions

- **GET `/characters`** → Character selection page.
- **GET `/chat/{character_id}`** → Chat UI for a character.
- **GET `/conversations`** → View user conversations.
- **GET `/create-character`** → Create character page.
- **POST `/login`** → Authenticate or auto-register a user.
- **POST `/api/create-character`** → Create a character.
- **POST `/api/send-message`** → Send a message via HTTP.

WebSocket

- **WS `/ws/chat/{user_id}/{character_id}/{conversation_id}`** → Real-time chat.

## Quickstart

1) Clone repo and move to project root.

2) Create a conda env (recommended).

```
conda env create -f backend/environment.yml
conda activate ai-character-backend
```

Alternatively, create manually:

```
conda create -n ai-character-backend python=3.10 -y
conda activate ai-character-backend
pip install -r requirements.txt  # uses root requirements
pip install -e backend[tests] || pip install pytest
```

3) Configure environment variables

- Copy `.env.example` to `.env` and fill in values as needed.
- The app reads env from `backend/.env` or project root `.env` via `pydantic.BaseSettings`.

```
cp backend/.env.example backend/.env
```

4) Run the unified server (API + Web)

```
python -m backend.main
# or with uvicorn
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

5) Try the demo client (requires server running on port 8000)

```
python backend/api_demo.py
```

6) Run tests

```
pytest -q backend
```

## Packaging

- `backend/pyproject.toml` (modern metadata) and `backend/setup.py` (legacy) are provided.
- Editable install from project root:

```
pip install -e backend
```

## Notes on Integration (LangChain, Groq, FAISS, HF)

- Replace `ChatService.generate_reply()` with real chain logic.
- Suggested flow:
  - Embed character memories/docs → store in FAISS (`data/vectorstore`).
  - Build Retrieval Augmented Generation chain with LangChain + Groq/HF.
  - Stream responses via FastAPI and Server-Sent Events if needed.

## Project Layout (Backend)

```
backend/
  api/
    v1/
      routes.py
  web/
    routes.py
  core/
    config.py
    logging.py
  service/
    chat_service.py
  model/
    schemas.py
  utils/
    faiss_helper.py
  tests/
    test_health.py
    test_chat_stub.py
  main.py
  api_demo.py
  pyproject.toml
  setup.py
  environment.yml
  .env.example
  pytest.ini
  README.md
```

## Security

- Do not commit real secrets. Use `.env` locally; only `.env.example` is versioned.
- Validate inputs with Pydantic models (`api/v1/routes.py`).

## License

MIT
