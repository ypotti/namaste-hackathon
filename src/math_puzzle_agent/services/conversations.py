"""Transactional conversation application service."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from math_puzzle_agent.db.models import Game, Message
from math_puzzle_agent.db.repositories import (
    ConversationRepository,
    GameRepository,
    GenerationRunRepository,
    MessageRepository,
)
from math_puzzle_agent.games.fixtures import CANONICAL_PROJECTILE_GAME
from math_puzzle_agent.games.html_renderer import render_game_html
from math_puzzle_agent.games.solvers.projectile import simulate_projectile


class ConversationGenerationService:
    """Complete the deterministic Phase 3 fixture generation atomically."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def submit_message(self, *, conversation_id, content: str) -> tuple[Message, Game, Message]:
        messages = MessageRepository(self.session)
        runs = GenerationRunRepository(self.session)

        user_message = await messages.create(
            conversation_id=conversation_id,
            role="user",
            content=content,
        )
        run = await runs.create(conversation_id=conversation_id)

        spec = CANONICAL_PROJECTILE_GAME
        result = simulate_projectile(spec)
        if not result.winnable:
            raise ValueError("canonical projectile fixture failed solver verification")
        solver_result = {
            "winnable": result.winnable,
            "closest_distance": result.closest_distance,
            "closest_point": result.closest_point.model_dump(mode="json"),
            "closest_step": result.closest_step,
            "solver_version": spec.solver_version,
        }
        spec_json = spec.model_dump(mode="json")
        game = Game(
            conversation_id=conversation_id,
            generation_run_id=run.id,
            schema_version=spec.schema_version,
            contract_version=spec.renderer_version,
            game_type=spec.game_type,
            title=spec.title,
            concept=spec.concept,
            spec=spec_json,
            generated_html=render_game_html(spec),
            verification_status="verified",
            solver_result=solver_result,
        )
        self.session.add(game)

        # Allocate the game UUID before it is referenced by the ready message.
        await self.session.flush()

        run.status = "completed"
        run.candidate_game_spec = spec_json
        run.solver_result = solver_result
        run.review_result = {"status": "approved", "mode": "canonical_fixture"}
        run.attempt_count = 1
        run.completed_at = datetime.now(UTC)

        assistant_message = await messages.create(
            conversation_id=conversation_id,
            role="assistant",
            content=f'Your game "{spec.title}" is ready.',
            metadata={"status": "ready", "run_id": str(run.id), "game_id": str(game.id)},
        )
        await self.session.flush()
        await self.session.refresh(game)
        return user_message, game, assistant_message
