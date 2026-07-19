"""Game endpoints used by the trusted React renderer."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from math_puzzle_agent.api.routes.conversations import GameRecordResponse
from math_puzzle_agent.db.repositories import GameRepository, get_session
from math_puzzle_agent.games.fixtures import CANONICAL_PUZZLE, DEMO_GAME_HTML
from math_puzzle_agent.schemas import PuzzleSpec


router = APIRouter(prefix="/games", tags=["games"])
Session = Annotated[AsyncSession, Depends(get_session)]


@router.get("/demo", response_model=PuzzleSpec)
async def get_demo_game() -> PuzzleSpec:
    """Return a solver-verified fixture through the production game contract."""

    return CANONICAL_PUZZLE


@router.get("/demo/content", response_class=Response)
async def get_demo_game_content() -> Response:
    return Response(DEMO_GAME_HTML, media_type="text/html")


@router.get("/{game_id}/content", response_class=Response)
async def get_game_content(game_id: uuid.UUID, session: Session) -> Response:
    """Serve a persisted game artifact for a sandboxed creator/learner iframe."""

    game = await GameRepository(session).get(game_id)
    if game is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")
    return Response(game.generated_html, media_type="text/html")


@router.get("/{game_id}", response_model=GameRecordResponse)
async def get_game(game_id: uuid.UUID, session: Session) -> GameRecordResponse:
    game = await GameRepository(session).get(game_id)
    if game is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")
    return GameRecordResponse.model_validate(game)


@router.get("", response_model=list[GameRecordResponse])
async def list_games(session: Session) -> list[GameRecordResponse]:
    """List all games stored in the database."""
    games = await GameRepository(session).list_all()
    return [GameRecordResponse.model_validate(g) for g in games]
