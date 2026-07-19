"""Read and stream persisted generation-run progress.

The workflow executor can update ``GenerationRun`` fields in its own transaction;
this service deliberately depends only on those persisted fields, so an API process
can reconnect to a run after a browser refresh or worker restart.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from datetime import datetime
from typing import Any, Final

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from math_puzzle_agent.db.models import Game, GenerationRun


TERMINAL_RUN_STATUSES: Final = frozenset({"completed", "failed", "cancelled", "needs_more_info"})
RunWorker = Callable[[uuid.UUID], Awaitable[None]]


def serialize_run(run: GenerationRun) -> dict[str, Any]:
    """Return the stable public representation of a generation run."""

    return {
        "schema_version": "1.0",
        "id": str(run.id),
        "conversation_id": str(run.conversation_id),
        "status": run.status,
        "attempt_count": run.attempt_count,
        "stage": (run.review_result or {}).get("stage"),
        "progress_event": (run.review_result or {}).get("progress_event"),
        "message": (run.review_result or {}).get("message"),
        "error": (
            {"code": run.error_code, "message": run.error_message}
            if run.error_code or run.error_message
            else None
        ),
        "started_at": _datetime(run.started_at),
        "completed_at": _datetime(run.completed_at),
    }


def _datetime(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


class GenerationRunService:
    """Query runs and expose resumable, versioned server-sent events."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, run_id: uuid.UUID) -> GenerationRun | None:
        return await self.session.get(GenerationRun, run_id)

    async def snapshot(self, run_id: uuid.UUID) -> dict[str, Any] | None:
        run = await self.get(run_id)
        if run is None:
            return None
        payload = serialize_run(run)
        payload["game_id"] = await self.session.scalar(
            select(Game.id).where(Game.generation_run_id == run_id).limit(1)
        )
        if payload["game_id"] is not None:
            payload["game_id"] = str(payload["game_id"])
        return payload

    async def events(
        self,
        run_id: uuid.UUID,
        *,
        after_version: int = 0,
        poll_interval: float = 0.5,
    ) -> AsyncIterator[str]:
        """Poll a run and emit changed snapshots until it reaches a terminal state."""

        version = max(after_version, 0)
        previous: str | None = None
        while True:
            run = await self.get(run_id)
            if run is None:
                return
            payload = await self.snapshot(run_id)
            if payload is None:
                return
            fingerprint = json.dumps(payload, sort_keys=True)
            if fingerprint != previous:
                version += 1
                event_name = _public_event_name(payload)
                event = {"event_version": version, **payload}
                yield f"id: {version}\nevent: {event_name}\ndata: {json.dumps(event)}\n\n"
                previous = fingerprint
            if run.status in TERMINAL_RUN_STATUSES:
                return
            await asyncio.sleep(poll_interval)
            # Ensure a long-lived request does not keep returning its identity-map copy.
            self.session.expire(run)


def _public_event_name(payload: dict[str, Any]) -> str:
    if payload.get("status") == "completed" and payload.get("game_id"):
        return "game.ready"
    if payload.get("status") == "failed":
        return "run.failed"
    if payload.get("status") == "needs_more_info":
        return "planner.needs_more_info"
    raw = payload.get("progress_event")
    if not isinstance(raw, str):
        return "run.updated"
    aliases = {
        "validation_started": "validator.started",
        "validation_completed": "validator.completed",
        "validation_failed": "validator.failed",
    }
    if raw in aliases:
        return aliases[raw]
    for suffix in ("_started", "_completed", "_failed"):
        if raw.endswith(suffix):
            return f"{raw.removesuffix(suffix)}.{suffix[1:]}"
    return "run.updated"


def launch_run(run_id: uuid.UUID, worker: RunWorker) -> asyncio.Task[None]:
    """Launch an injected workflow worker without coupling routes to LangGraph."""

    return asyncio.create_task(worker(run_id), name=f"generation-run-{run_id}")
