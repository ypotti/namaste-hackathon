"""Generation-run status and progress endpoints."""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from math_puzzle_agent.db.repositories import get_session
from math_puzzle_agent.services.generation_runs import GenerationRunService, serialize_run


router = APIRouter(prefix="/runs", tags=["generation-runs"])
Session = Annotated[AsyncSession, Depends(get_session)]


@router.get("/{run_id}")
async def get_run(run_id: uuid.UUID, session: Session) -> dict[str, Any]:
    payload = await GenerationRunService(session).snapshot(run_id)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Generation run not found")
    return payload


@router.get("/{run_id}/events")
async def stream_run_events(
    run_id: uuid.UUID,
    session: Session,
    last_event_id: Annotated[str | None, Header(alias="Last-Event-ID")] = None,
) -> StreamingResponse:
    service = GenerationRunService(session)
    if await service.get(run_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Generation run not found")
    try:
        after_version = int(last_event_id or 0)
    except ValueError:
        raise HTTPException(status_code=400, detail="Last-Event-ID must be an integer") from None
    return StreamingResponse(
        service.events(run_id, after_version=after_version),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
