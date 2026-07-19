"""PostgreSQL-backed LangGraph checkpoint lifecycle helpers."""

from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver


def checkpoint_database_url(database_url: str) -> str:
    """Convert SQLAlchemy driver URLs to a psycopg-compatible PostgreSQL URL."""

    return database_url.replace("postgresql+asyncpg://", "postgresql://", 1).replace(
        "postgresql+psycopg://", "postgresql://", 1
    )


@asynccontextmanager
async def postgres_checkpointer(database_url: str) -> AsyncIterator[Any]:
    """Open a checkpointer for application/workflow lifespan management."""

    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

    async with AsyncPostgresSaver.from_conn_string(checkpoint_database_url(database_url)) as saver:
        yield saver


async def setup_postgres_checkpoints(database_url: str) -> None:
    """Create/update LangGraph checkpoint tables (deployment/setup operation)."""

    async with postgres_checkpointer(database_url) as saver:
        await saver.setup()


def postgres_checkpointer_sync(database_url: str):
    """Return the sync saver context manager for workflows running in a worker thread."""

    from langgraph.checkpoint.postgres import PostgresSaver

    return PostgresSaver.from_conn_string(checkpoint_database_url(database_url))
