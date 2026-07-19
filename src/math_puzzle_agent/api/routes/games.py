"""Game endpoints used by the trusted React renderer."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from math_puzzle_agent.api.routes.conversations import GameRecordResponse
from math_puzzle_agent.db.repositories import GameRepository, get_session
from math_puzzle_agent.games.fixtures import CANONICAL_PROJECTILE_GAME
from math_puzzle_agent.games.schemas import GameSpecV1


router = APIRouter(prefix="/games", tags=["games"])
Session = Annotated[AsyncSession, Depends(get_session)]


@router.get("/demo", response_model=GameSpecV1)
async def get_demo_game() -> GameSpecV1:
    """Return a solver-verified fixture through the production game contract."""

    return CANONICAL_PROJECTILE_GAME


@router.get("/{game_id}", response_model=GameRecordResponse)
async def get_game(game_id: uuid.UUID, session: Session) -> GameRecordResponse:
    game = await GameRepository(session).get(game_id)
    if game is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")
    return GameRecordResponse.model_validate(game)
