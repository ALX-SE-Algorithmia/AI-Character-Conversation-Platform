import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI

from backend.api.v1.routes import router as api_v1_router
from backend.core.config import get_settings
from backend.core.logging import configure_logging
from backend.service.container import get_platform


@asynccontextmanager  # pragma: no cover
async def lifespan(app: FastAPI):
    platform = get_platform()
    import asyncio
    asyncio.create_task(platform.cleanup_task())
    yield


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(title="AI Character Backend", version="0.1.0", lifespan=lifespan)

    # API router only (web UI removed)
    app.include_router(api_v1_router, prefix="/api/v1", tags=["v1"])

    return app


app = create_app()


if __name__ == "__main__":  # pragma: no cover
    settings = get_settings()
    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
    )
