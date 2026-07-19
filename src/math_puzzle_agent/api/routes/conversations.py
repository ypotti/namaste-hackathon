"""Conversation, message, and conversation-game endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from math_puzzle_agent.db.repositories import (
    ConversationRepository,
    GameRepository,
    GenerationRunRepository,
    MessageRepository,
    get_session,
)
from math_puzzle_agent.games.schemas import GameSpecV1, parse_game_spec_v1
from math_puzzle_agent.services.conversations import ConversationGenerationService
from math_puzzle_agent.services.generation_runs import launch_run
from math_puzzle_agent.services.structured_generation import execute_structured_generation


router = APIRouter(prefix="/conversations", tags=["conversations"])
Session = Annotated[AsyncSession, Depends(get_session)]


class ConversationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    title: str | None = Field(default=None, min_length=1, max_length=120)


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    title: str | None
    status: str
    created_at: datetime
    updated_at: datetime


class MessageCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    content: str = Field(min_length=1, max_length=2000)


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    conversation_id: uuid.UUID
    role: str
    content: str
    metadata: dict[str, Any] = Field(validation_alias="message_metadata")
    created_at: datetime


class GameRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    conversation_id: uuid.UUID
    generation_run_id: uuid.UUID
    schema_version: str
    contract_version: str
    game_type: str
    title: str
    concept: str
    verification_status: str
    solver_result: dict[str, Any]
    spec: GameSpecV1
    created_at: datetime
    updated_at: datetime


class ReadyMessageResponse(BaseModel):
    status: Literal["ready"] = "ready"
    run_id: uuid.UUID
    game_id: uuid.UUID
    game: GameSpecV1
    assistant_message: MessageResponse


class ProcessingMessageResponse(BaseModel):
    status: Literal["processing"] = "processing"
    run_id: uuid.UUID


MessageSubmissionResponse = ReadyMessageResponse | ProcessingMessageResponse


async def _active_conversation(session: AsyncSession, conversation_id: uuid.UUID):
    conversation = await ConversationRepository(session).get_active(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return conversation


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    session: Session,
    payload: ConversationCreate | None = None,
) -> ConversationResponse:
    async with session.begin():
        conversation = await ConversationRepository(session).create(
            title=payload.title if payload is not None else None
        )
    return ConversationResponse.model_validate(conversation)


@router.get("", response_model=list[ConversationResponse])
async def list_conversations(session: Session) -> list[ConversationResponse]:
    conversations = await ConversationRepository(session).list_active()
    return [ConversationResponse.model_validate(item) for item in conversations]


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(conversation_id: uuid.UUID, session: Session) -> ConversationResponse:
    conversation = await _active_conversation(session, conversation_id)
    return ConversationResponse.model_validate(conversation)


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(conversation_id: uuid.UUID, session: Session) -> Response:
    async with session.begin():
        conversation = await _active_conversation(session, conversation_id)
        await ConversationRepository(session).soft_delete(conversation)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{conversation_id}/messages", response_model=list[MessageResponse])
async def list_messages(conversation_id: uuid.UUID, session: Session) -> list[MessageResponse]:
    await _active_conversation(session, conversation_id)
    messages = await MessageRepository(session).list_for_conversation(conversation_id)
    return [MessageResponse.model_validate(item) for item in messages]


@router.post("/{conversation_id}/messages", response_model=MessageSubmissionResponse)
async def create_message(
    conversation_id: uuid.UUID,
    payload: MessageCreate,
    session: Session,
    request: Request,
) -> MessageSubmissionResponse:
    settings = request.app.state.settings
    if settings.model_generation_enabled:
        async with session.begin():
            await _active_conversation(session, conversation_id)
            await MessageRepository(session).create(
                conversation_id=conversation_id,
                role="user",
                content=payload.content,
            )
            run = await GenerationRunRepository(session).create(conversation_id=conversation_id)
        database = request.app.state.database
        launch_run(
            run.id,
            lambda run_id: execute_structured_generation(
                database=database,
                settings=settings,
                run_id=run_id,
                conversation_id=conversation_id,
                content=payload.content,
            ),
        )
        return ProcessingMessageResponse(run_id=run.id)

    async with session.begin():
        await _active_conversation(session, conversation_id)
        _, game, assistant = await ConversationGenerationService(session).submit_message(
            conversation_id=conversation_id,
            content=payload.content,
        )
    return ReadyMessageResponse(
        run_id=game.generation_run_id,
        game_id=game.id,
        game=parse_game_spec_v1(game.spec),
        assistant_message=MessageResponse.model_validate(assistant),
    )


@router.get("/{conversation_id}/games", response_model=list[GameRecordResponse])
async def list_conversation_games(
    conversation_id: uuid.UUID,
    session: Session,
) -> list[GameRecordResponse]:
    await _active_conversation(session, conversation_id)
    games = await GameRepository(session).list_for_conversation(conversation_id)
    return [GameRecordResponse.model_validate(item) for item in games]
