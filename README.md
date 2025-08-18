<div align="center">

  <h1>AI Character Conversation Platform ✨</h1>

  <p>A modern, modular AI chat platform with character‑driven conversations.</p>

  <p>
    <img alt="Python" src="https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white" />
    <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-API%20First-009688?logo=fastapi&logoColor=white" />
    <img alt="Tests" src="https://img.shields.io/badge/Tests-Pytest%20%2B%20Coverage-6A5ACD" />
    <img alt="License" src="https://img.shields.io/badge/License-MIT-black" />
  </p>

  <sub>API‑only backend (no HTML templates or WebSockets) so frontend teams can integrate freely.</sub>
</div>

---

## 🧭 Table of Contents

- [Highlights](#-highlights)
- [Quickstart](#-quickstart)
- [API Endpoints](#-api-endpoints)
- [Architecture](#-architecture)
- [Configuration](#%EF%B8%8F-configuration)
- [Testing & Coverage](#-testing--coverage)
- [Roadmap](#%EF%B8%8F-roadmap)
- [Screenshots](#-screenshots)
- [Contributing](#-contributing)
- [License](#-license)
- [Acknowledgements](#-acknowledgements)

---

## 🚀 Highlights

- **FastAPI, production-ready**: Modular `api`, `service`, `core`, `model` layers.
- **Character-driven chat**: Predefined characters via `data/characters.json` (e.g., `coach`).
- **LLM stub mode**: Works offline; echoes responses for rapid dev/testing.
- **Clean orchestration**: `PlatformService` composes domain services.
- **Thorough tests**: Pytest with coverage; CI-friendly.

---

## 📦 Quickstart

1) Clone and enter the repo

```bash
git clone https://github.com/yourusername/ai-character-platform.git
cd ai-character-platform
```

2) Create environment (Conda or venv)

```bash
# Conda (recommended)
conda env create -f backend/environment.yml
conda activate ai-character-backend

# OR venv + pip
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -e backend
```

3) Configure environment variables (optional)

```bash
cp backend/.env.example backend/.env
# LLMService runs in stub mode if no GROQ_API_KEY is provided
```

4) Run the server

```bash
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

5) Try the demo client

```bash
python backend/api_demo.py
# or point to a custom server
BACKEND_BASE_URL=http://127.0.0.1:8000/api/v1 python backend/api_demo.py
```

---

## 🔌 API Endpoints

Base path: `/api/v1`

- `GET /health` — Service health/status
- `POST /chat` — Body: `{ "character_id": "coach", "message": "Hello" }`

Example cURL:

```bash
curl -s http://127.0.0.1:8000/api/v1/health | jq .

curl -s -X POST http://127.0.0.1:8000/api/v1/chat \
  -H 'Content-Type: application/json' \
  -d '{"character_id":"coach","message":"Hello there!"}' | jq .
```

> Tip: No API key? The LLM stub mode returns an echo‑style reply so you can build end‑to‑end without external dependencies.

---

## 🧱 Architecture

```
backend/
  api/
    v1/
      routes.py           # FastAPI routes (health, chat)
  core/
    config.py             # Pydantic settings (.env)
    logging.py            # Logging bootstrap
  model/
    schemas.py            # Pydantic domain models
  service/
    character_service.py  # Load/generate characters
    conversation_service.py# Conversation lifecycle & persistence
    llm_service.py        # LLM wrapper (Groq, stub mode)
    platform_service.py   # Orchestrator
  main.py                 # FastAPI app factory (API-only)
data/
  characters.json         # Predefined characters
  conversations/          # Conversation JSON persistence (default)
```

Notes:
- Storage defaults to JSON under `data/`. Upcoming: optional SQLite.
- `LLMService` stub mode returns an echo response for local testing.

---

## ⚙️ Configuration

Environment variables (via `backend/.env`):

- `APP_NAME`, `APP_VERSION`, `ENVIRONMENT`
- `HOST`, `PORT`, `RELOAD`
- `GROQ_API_KEY` (optional; omit to use stub mode)

> Optional: Set `BACKEND_BASE_URL` when running `backend/api_demo.py` against a non‑default host/port.

---

## 🧪 Testing & Coverage

```bash
pytest --cov=backend --cov-report=term-missing backend
```

The suite covers API, services, and utilities. Stub mode ensures tests run offline.

---

## 🛣️ Roadmap

- [ ] Optional SQLite persistence for conversations/messages
- [ ] Rich retrieval + embeddings integration
- [ ] Streaming responses
- [ ] AuthN/AuthZ hardening

---

## 🖼️ Screenshots

> Placeholder space for frontend integration shots. Add your UI captures here:

- Service Health (REST client or Swagger UI)
- Chat workflow from the consuming frontend

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Create a feature branch: `git checkout -b feat/short-name`
2. Run tests: `pytest --cov=backend backend`
3. Open a PR with a concise description and screenshots/logs when helpful

## 📝 License

MIT

---

## 🙏 Acknowledgements

- [FastAPI](https://fastapi.tiangolo.com/)
- [Groq](https://groq.com/)
- [Llama 3](https://ai.meta.com/llama/)