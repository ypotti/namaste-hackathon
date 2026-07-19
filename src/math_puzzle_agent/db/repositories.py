"""Async persistence primitives for conversations and generated games."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Conversation, Game, GenerationRun, Message


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Provide one request-scoped database session."""

    factory = request.app.state.database.session_factory
    if factory is None:
        raise RuntimeError("database has not been started")
    async with factory() as session:
        yield session


class ConversationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, *, title: str | None = None) -> Conversation:
        conversation = Conversation(title=title, status="active")
        self.session.add(conversation)
        await self.session.flush()
        await self.session.refresh(conversation)
        return conversation

    async def list_active(self) -> list[Conversation]:
        result = await self.session.scalars(
            select(Conversation)
            .where(Conversation.deleted_at.is_(None))
            .order_by(Conversation.updated_at.desc(), Conversation.created_at.desc())
        )
        return list(result)

    async def get_active(self, conversation_id: uuid.UUID) -> Conversation | None:
        return await self.session.scalar(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.deleted_at.is_(None),
            )
        )

    async def soft_delete(self, conversation: Conversation) -> None:
        conversation.status = "deleted"
        conversation.deleted_at = datetime.now(UTC)
        await self.session.flush()


class MessageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        conversation_id: uuid.UUID,
        role: str,
        content: str,
        metadata: dict[str, object] | None = None,
    ) -> Message:
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            message_metadata=metadata or {},
        )
        self.session.add(message)
        await self.session.flush()
        await self.session.refresh(message)
        return message

    async def list_for_conversation(self, conversation_id: uuid.UUID) -> list[Message]:
        result = await self.session.scalars(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at, Message.id)
        )
        return list(result)


class GenerationRunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, *, conversation_id: uuid.UUID) -> GenerationRun:
        run = GenerationRun(conversation_id=conversation_id, status="processing")
        self.session.add(run)
        await self.session.flush()
        return run


class GameRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, game_id: uuid.UUID) -> Game | None:
        return await self.session.get(Game, game_id)

    async def list_for_conversation(self, conversation_id: uuid.UUID) -> list[Game]:
        result = await self.session.scalars(
            select(Game)
            .where(Game.conversation_id == conversation_id)
            .order_by(Game.created_at.desc(), Game.id.desc())
        )
        return list(result)

    async def list_all(self) -> list[Game]:
        result = await self.session.scalars(
            select(Game)
            .order_by(Game.created_at.desc(), Game.id.desc())
        )
        return list(result)
