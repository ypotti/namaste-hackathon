from __future__ import annotations

from collections import deque
import pytest

from math_puzzle_agent.schemas import PlannerDecision, PuzzleSpec, ReviewerDecision
from math_puzzle_agent.games.fixtures import CANONICAL_PUZZLE
from math_puzzle_agent.structured_workflow import StructuredGameWorkflow


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

    def invoke(self, _messages):
        if not hasattr(self, "_values_deque"):
            self._values_deque = deque(self.values)
        value = self._values_deque.popleft()
        if isinstance(value, Exception):
            raise value
        
        class MockMessage:
            def __init__(self, content):
                self.content = content
        return MockMessage(value)


def workflow(*, planner, generator=(), reviewer=(), attempts=3, progress=None):
    return StructuredGameWorkflow(
        planner_llm=FakeLLM(planner),
        designer_llm=FakeLLM(generator),
        reviewer_llm=FakeLLM(reviewer),
        max_attempts=attempts,
        progress=progress,
    )


def test_returns_ready_workflow_state():
    spec = CANONICAL_PUZZLE
    html_content = "<html><body>Check answer</body></html>"
    app = workflow(
        planner=[PlannerDecision(status="ready", puzzle_spec=spec)],
        generator=[html_content],
        reviewer=[ReviewerDecision(approved=True)],
    )

    result = app.invoke("Make a triangle game")

    assert result["status"] == "ready"
    assert result["spec"] == spec
    assert result["generated_html"] == html_content


def test_returns_clarification_without_generating():
    app = workflow(
        planner=[PlannerDecision(status="need_more_info", next_question="Which legs?")]
    )
    result = app.invoke("Make a right triangle game")
    assert result["status"] == "needs_more_info"
    assert result["message"] == "Which legs?"
    assert "spec" not in result


def test_blank_request_never_calls_models():
    app = workflow(planner=[])
    result = app.invoke("  ")
    assert result["status"] == "needs_more_info"


def test_invoke_synchronizes_thread_id():
    app = workflow(planner=[PlannerDecision(status="need_more_info", next_question="What legs?")])
    assert app.cfg.thread_id != "puzzle-test-123"
    app.invoke("Teach triangle", thread_id="puzzle-test-123")
    assert app.cfg.thread_id == "puzzle-test-123"
