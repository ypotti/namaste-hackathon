"""Application-domain SQLAlchemy models."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    messages: Mapped[list[Message]] = relationship(back_populates="conversation", cascade="all, delete-orphan")
    runs: Mapped[list[GenerationRun]] = relationship(back_populates="conversation", cascade="all, delete-orphan")
    games: Mapped[list[Game]] = relationship(back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (Index("ix_messages_conversation_created", "conversation_id", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, nullable=False, default=dict, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    conversation: Mapped[Conversation] = relationship(back_populates="messages")


class GenerationRun(Base):
    __tablename__ = "generation_runs"
    __table_args__ = (
        Index("ix_generation_runs_conversation_started", "conversation_id", "started_at"),
        Index("ix_generation_runs_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="pending")
    puzzle_spec: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    candidate_game_spec: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    solver_result: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    review_result: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    error_code: Mapped[str | None] = mapped_column(Text)
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    conversation: Mapped[Conversation] = relationship(back_populates="runs")
    games: Mapped[list[Game]] = relationship(back_populates="generation_run", cascade="all, delete-orphan")


class Game(Base):
    __tablename__ = "games"
    __table_args__ = (
        Index("ix_games_conversation_created", "conversation_id", "created_at"),
        Index("ix_games_game_type", "game_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    generation_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("generation_runs.id", ondelete="CASCADE"), nullable=False)
    schema_version: Mapped[str] = mapped_column(Text, nullable=False)
    contract_version: Mapped[str] = mapped_column(Text, nullable=False)
    game_type: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    concept: Mapped[str] = mapped_column(Text, nullable=False)
    spec: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    verification_status: Mapped[str] = mapped_column(Text, nullable=False)
    solver_result: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    conversation: Mapped[Conversation] = relationship(back_populates="games")
    generation_run: Mapped[GenerationRun] = relationship(back_populates="games")
