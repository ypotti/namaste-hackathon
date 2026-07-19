from __future__ import annotations

from collections import deque

import pytest

from math_puzzle_agent.games.fixtures import CANONICAL_GAMES, CANONICAL_PROJECTILE_GAME
from math_puzzle_agent.structured_workflow import (
    GameReviewV1,
    PlannerDecisionV1,
    StructuredGameWorkflow,
)


class FakeStructured:
    def __init__(self, values):
        self.values = deque(values)

    def invoke(self, _messages):
        value = self.values.popleft()
        if isinstance(value, Exception):
            raise value
        return value


class FakeLLM:
    def __init__(self, values):
        self.values = values
        self.requested_schema = None

    def with_structured_output(self, schema):
        self.requested_schema = schema
        return FakeStructured(self.values)


def workflow(*, planner, designer=(), reviewer=(), attempts=3, progress=None):
    return StructuredGameWorkflow(
        planner_llm=FakeLLM(planner),
        designer_llm=FakeLLM(designer),
        reviewer_llm=FakeLLM(reviewer),
        max_attempts=attempts,
        progress=progress,
    )


def ready_decision():
    return PlannerDecisionV1(
        status="ready",
        design_brief="Teach middle-school projectile motion with an elevated target.",
        mechanic="projectile_target",
    )


@pytest.mark.parametrize("spec", CANONICAL_GAMES, ids=lambda spec: spec.game_type)
def test_every_supported_mechanic_is_solver_verified(spec):
    app = workflow(
        planner=[PlannerDecisionV1(
            status="ready",
            design_brief=f"Teach with {spec.game_type}.",
            mechanic=spec.game_type,
        )],
        designer=[spec],
        reviewer=[GameReviewV1(approved=True)],
    )

    result = app.invoke(f"Build a {spec.game_type} game")

    assert result["status"] == "ready"
    assert result["spec"] == spec


def test_returns_clarification_without_designing():
    app = workflow(
        planner=[PlannerDecisionV1(status="needs_more_info", next_question="Which age group?")]
    )
    result = app.invoke("Make a physics game")
    assert result["status"] == "needs_more_info"
    assert result["message"] == "Which age group?"
    assert "spec" not in result


def test_returns_solver_verified_spec_and_progress_events():
    events = []
    app = workflow(
        planner=[ready_decision()],
        designer=[CANONICAL_PROJECTILE_GAME],
        reviewer=[GameReviewV1(approved=True)],
        progress=lambda event, details: events.append((event, details)),
    )
    result = app.invoke("Teach projectile motion")
    assert result["status"] == "ready"
    assert result["spec"] == CANONICAL_PROJECTILE_GAME
    assert [event for event, _ in events] == [
        "planner_started",
        "planner_completed",
        "designer_started",
        "validation_started",
        "validation_completed",
        "reviewer_started",
        "reviewer_completed",
    ]


def test_reviewer_rejection_causes_bounded_repair():
    revised = CANONICAL_PROJECTILE_GAME.model_copy(update={"title": "Revised Arc"})
    app = workflow(
        planner=[ready_decision()],
        designer=[CANONICAL_PROJECTILE_GAME, revised],
        reviewer=[
            GameReviewV1(approved=False, feedback="Use a clearer title"),
            GameReviewV1(approved=True),
        ],
        attempts=2,
    )
    result = app.invoke("Teach projectile motion")
    assert result["status"] == "ready"
    assert result["attempts"] == 2
    assert result["spec"].title == "Revised Arc"


def test_unwinnable_output_fails_after_attempt_limit():
    impossible = CANONICAL_PROJECTILE_GAME.model_copy(
        update={
            "physics": CANONICAL_PROJECTILE_GAME.physics.model_copy(
                update={"target_x": 735, "target_y": 90}
            ),
            "solution": CANONICAL_PROJECTILE_GAME.solution.model_copy(
                update={"angle": 20, "power": 55}
            ),
        }
    )
    app = workflow(planner=[ready_decision()], designer=[impossible], attempts=1)
    result = app.invoke("Teach projectile motion")
    assert result["status"] == "failed"
    assert "No valid game" in result["message"]


def test_unsupported_concept_is_explicit_planner_clarification():
    question = "Only projectile-target is supported; should I adapt fractions to trajectory ratios?"
    app = workflow(
        planner=[PlannerDecisionV1(status="needs_more_info", next_question=question)]
    )
    result = app.invoke("Create a fraction pizza game")
    assert result == {
        "request": "Create a fraction pizza game",
        "decision": result["decision"],
        "status": "needs_more_info",
        "message": question,
    }


def test_refused_planner_output_becomes_failure():
    app = workflow(planner=[None])
    result = app.invoke("Teach motion")
    assert result["status"] == "failed"
    assert "refused" in result["message"]


def test_blank_request_never_calls_models():
    app = workflow(planner=[])
    result = app.invoke("  ")
    assert result["status"] == "needs_more_info"
