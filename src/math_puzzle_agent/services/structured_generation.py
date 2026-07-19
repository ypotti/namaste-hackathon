"""Execute the structured game workflow and persist its terminal outcome."""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime
from typing import Any

from math_puzzle_agent.api.settings import APISettings
from math_puzzle_agent.db.models import Game, GenerationRun
from math_puzzle_agent.db.checkpoints import postgres_checkpointer_sync
from math_puzzle_agent.db.repositories import MessageRepository
from math_puzzle_agent.games.registry import solve_game
from math_puzzle_agent.games.html_renderer import render_game_html
from math_puzzle_agent.structured_workflow import create_openai_structured_workflow


async def execute_structured_generation(
    *, database: Any, settings: APISettings, run_id: uuid.UUID, conversation_id: uuid.UUID, content: str
) -> None:
    """Run synchronous model calls off-loop while persisting reconnectable progress."""

    if database.session_factory is None:
        raise RuntimeError("database has not been started")
    loop = asyncio.get_running_loop()

    async def save_progress(event: str, details: dict[str, Any]) -> None:
        async with database.session_factory() as session, session.begin():
            run = await session.get(GenerationRun, run_id)
            if run is not None:
                run.review_result = {"progress_event": event, "stage": _stage(event), "details": details}
                if isinstance(details.get("attempt"), int):
                    run.attempt_count = details["attempt"]

    def progress(event: str, details: dict[str, Any]) -> None:
        asyncio.run_coroutine_threadsafe(save_progress(event, details), loop).result(timeout=10)

    try:
        async with database.session_factory() as session:
            messages = await MessageRepository(session).list_for_conversation(conversation_id)
        request_text = _conversation_prompt(messages) or content

        def run_workflow() -> dict[str, Any]:
            with postgres_checkpointer_sync(settings.database_url) as checkpointer:
                checkpointer.setup()
                workflow = create_openai_structured_workflow(
                    planner_model=settings.planner_model,
                    designer_model=settings.designer_model,
                    reviewer_model=settings.reviewer_model,
                    max_attempts=settings.max_generation_attempts,
                    progress=progress,
                    api_key=settings.openai_api_key.get_secret_value() if settings.openai_api_key else None,
                    checkpointer=checkpointer,
                )
                return workflow.invoke(request_text, thread_id=str(run_id))

        result = await asyncio.wait_for(
            asyncio.to_thread(run_workflow), timeout=settings.workflow_timeout_seconds
        )
        await _persist_result(database, run_id, conversation_id, result)
    except TimeoutError:
        await _persist_failure(
            database, run_id,
            f"Game generation exceeded the {settings.workflow_timeout_seconds:g}-second timeout",
            error_code="generation_timeout",
        )
    except Exception as exc:
        await _persist_failure(database, run_id, str(exc))


async def _persist_result(database: Any, run_id: uuid.UUID, conversation_id: uuid.UUID, result: dict[str, Any]) -> None:
    async with database.session_factory() as session, session.begin():
        run = await session.get(GenerationRun, run_id)
        if run is None:
            return
        messages = MessageRepository(session)
        status = result.get("status")
        if status == "ready" and result.get("spec") is not None:
            spec = result["spec"]
            solved = solve_game(spec)
            solver_result = _jsonable_solver_result(solved)
            solver_result["solver_version"] = spec.solver_version
            game = Game(
                conversation_id=conversation_id,
                generation_run_id=run_id,
                schema_version=spec.schema_version,
                contract_version=spec.renderer_version,
                game_type=spec.game_type,
                title=spec.title,
                concept=spec.concept,
                spec=spec.model_dump(mode="json"),
                generated_html=render_game_html(spec),
                verification_status="verified",
                solver_result=solver_result,
            )
            session.add(game)
            await session.flush()
            run.status = "completed"
            run.candidate_game_spec = game.spec
            run.solver_result = solver_result
            run.review_result = {"progress_event": "game_ready", "stage": "completed", "game_id": str(game.id)}
            await messages.create(
                conversation_id=conversation_id,
                role="assistant",
                content=f'Your game "{spec.title}" is ready.',
                metadata={"status": "ready", "run_id": str(run_id), "game_id": str(game.id)},
            )
        elif status == "needs_more_info":
            question = str(result.get("message") or "What detail should I use?")
            run.status = "needs_more_info"
            run.review_result = {
                "progress_event": "planner_needs_more_info",
                "stage": "planner",
                "message": question,
            }
            await messages.create(
                conversation_id=conversation_id,
                role="assistant",
                content=question,
                metadata={"status": "needs_more_info", "run_id": str(run_id)},
            )
        else:
            run.status = "failed"
            run.error_code = "generation_failed"
            run.error_message = str(result.get("message") or "Game generation failed")
            run.review_result = {"progress_event": "run_failed", "stage": "failed"}
        run.completed_at = datetime.now(UTC)


async def _persist_failure(
    database: Any, run_id: uuid.UUID, message: str, *, error_code: str = "generation_exception"
) -> None:
    async with database.session_factory() as session, session.begin():
        run = await session.get(GenerationRun, run_id)
        if run is not None:
            run.status = "failed"
            run.error_code = error_code
            run.error_message = message[:1000]
            run.review_result = {"progress_event": "run_failed", "stage": "failed"}
            run.completed_at = datetime.now(UTC)


def _stage(event: str) -> str:
    return event.split("_", 1)[0]


def _jsonable_solver_result(result: Any) -> dict[str, Any]:
    values = result._asdict()
    return {
        key: value.model_dump(mode="json") if hasattr(value, "model_dump") else value
        for key, value in values.items()
    }


def _conversation_prompt(messages: list[Any]) -> str:
    """Give the planner the same multi-turn context users get in the CLI."""

    lines = [
        f"{message.role.capitalize()}: {message.content.strip()}"
        for message in messages
        if message.role in {"user", "assistant"} and message.content.strip()
    ]
    return "Conversation so far:\n" + "\n".join(lines) if lines else ""
