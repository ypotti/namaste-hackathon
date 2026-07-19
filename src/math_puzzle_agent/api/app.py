"""FastAPI application factory and service lifecycle."""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from math_puzzle_agent.api.routes.conversations import router as conversations_router
from math_puzzle_agent.api.routes.games import router as games_router
from math_puzzle_agent.api.routes.runs import router as runs_router
from math_puzzle_agent.api.routes.system import router as system_router
from math_puzzle_agent.api.settings import APISettings
from math_puzzle_agent.api.errors import install_error_handlers
from math_puzzle_agent.api.middleware import APIBoundaryMiddleware
from math_puzzle_agent.api.security import InMemoryFixedWindowRateLimiter
from math_puzzle_agent.db.session import Database


def create_app(settings: APISettings | None = None, database: Database | None = None) -> FastAPI:
    settings = settings or APISettings()
    database = database or Database(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.database = database
        app.state.settings = settings
        await database.start()
        try:
            yield
        finally:
            await database.close()

    app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
    install_error_handlers(app)
    app.add_middleware(
        APIBoundaryMiddleware,
        settings=settings,
        rate_limiter=InMemoryFixedWindowRateLimiter(
            settings.generation_rate_limit_requests,
            settings.generation_rate_limit_window_seconds,
        ),
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "X-Request-ID"],
    )
    app.include_router(system_router, prefix="/api/v1")
    app.include_router(conversations_router, prefix="/api/v1")
    app.include_router(games_router, prefix="/api/v1")
    app.include_router(runs_router, prefix="/api/v1")
    return app


app = create_app()


def main() -> None:
    """Run the development API using the project's console script."""

    import uvicorn

    uvicorn.run(
        "math_puzzle_agent.api.app:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
