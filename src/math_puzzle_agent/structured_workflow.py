"""LangGraph workflow that produces trusted, solver-proven game specifications.

LLMs are injected, making this module usable by FastAPI and deterministic in tests.
It deliberately does not replace the legacy HTML workflow or CLI.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Literal, Protocol, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, ConfigDict, Field, RootModel, ValidationError

from .game_prompts import DESIGNER_PROMPT, PLANNER_PROMPT, REPAIR_PROMPT, REVIEWER_PROMPT
from .games.registry import solve_game
from .games.schemas import GameSpecV1, parse_game_spec_v1

ProgressCallback = Callable[[str, dict[str, Any]], None]


class StructuredModel(Protocol):
    def invoke(self, input: Any, **kwargs: Any) -> Any: ...


class StructuredCapableModel(Protocol):
    def with_structured_output(self, schema: type[BaseModel]) -> StructuredModel: ...


class PlannerDecisionV1(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)
    status: Literal["needs_more_info", "ready"]
    next_question: str | None = Field(default=None, max_length=240)
    design_brief: str | None = Field(default=None, max_length=1200)
    mechanic: Literal[
        "projectile_target", "falling_object", "balance_torque",
        "momentum_collision", "fraction_grouping", "graph_match",
    ] | None = None

    def model_post_init(self, __context: Any) -> None:
        if self.status == "ready" and (not self.design_brief or self.mechanic is None):
            raise ValueError("ready decisions require a brief and supported mechanic")
        if self.status == "needs_more_info" and not self.next_question:
            raise ValueError("needs_more_info decisions require a question")


class GameReviewV1(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)
    approved: bool
    feedback: str = Field(default="", max_length=600)


class GameSpecEnvelopeV1(RootModel[GameSpecV1]):
    """Structured-output wrapper preserving the discriminated game union."""


class WorkflowState(TypedDict, total=False):
    request: str
    decision: PlannerDecisionV1
    spec: GameSpecV1
    candidate: object
    attempts: int
    feedback: str
    review: GameReviewV1
    status: Literal["needs_more_info", "ready", "failed"]
    message: str


class StructuredGameWorkflow:
    """Build and run the bounded structured-generation graph."""

    def __init__(
        self,
        *,
        planner_llm: StructuredCapableModel,
        designer_llm: StructuredCapableModel,
        reviewer_llm: StructuredCapableModel,
        max_attempts: int = 3,
        progress: ProgressCallback | None = None,
        checkpointer: Any | None = None,
    ) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least one")
        self.planner = planner_llm.with_structured_output(PlannerDecisionV1)
        self.designer = designer_llm.with_structured_output(GameSpecEnvelopeV1)
        self.reviewer = reviewer_llm.with_structured_output(GameReviewV1)
        self.max_attempts = max_attempts
        self.progress = progress or (lambda _event, _details: None)
        self.checkpointer = checkpointer
        self.graph = self._build_graph()

    def _emit(self, event: str, **details: Any) -> None:
        self.progress(event, details)

    @staticmethod
    def _coerce(value: object, model: type[BaseModel]) -> BaseModel:
        if value is None:
            raise ValueError("model refused to return structured output")
        if isinstance(value, model):
            return value
        return model.model_validate(value, strict=True)

    def _build_graph(self):
        graph = StateGraph(WorkflowState)

        def plan(state: WorkflowState) -> dict[str, Any]:
            self._emit("planner_started")
            try:
                raw = self.planner.invoke([
                    SystemMessage(content=PLANNER_PROMPT),
                    HumanMessage(content=state["request"]),
                ])
                decision = self._coerce(raw, PlannerDecisionV1)
            except Exception as exc:  # malformed output and provider refusals are user-safe
                self._emit("failed", stage="planner", reason=str(exc))
                return {"status": "failed", "message": f"Planner output was invalid: {exc}"}
            self._emit("planner_completed", status=decision.status)
            if decision.status == "needs_more_info":
                return {
                    "decision": decision,
                    "status": "needs_more_info",
                    "message": decision.next_question,
                }
            return {"decision": decision, "attempts": 0}

        def design(state: WorkflowState) -> dict[str, Any]:
            attempt = state.get("attempts", 0) + 1
            self._emit("designer_started", attempt=attempt)
            brief = state["decision"].design_brief or state["request"]
            content = f"Required mechanic: {state['decision'].mechanic}\nBrief: {brief}"
            messages = [SystemMessage(content=DESIGNER_PROMPT), HumanMessage(content=content)]
            if state.get("feedback"):
                messages.extend([
                    SystemMessage(content=REPAIR_PROMPT),
                    HumanMessage(content=f"Feedback: {state['feedback']}"),
                ])
            try:
                candidate = self.designer.invoke(messages)
                if isinstance(candidate, GameSpecEnvelopeV1):
                    candidate = candidate.root
            except Exception as exc:  # provider refusals/errors become a bounded failure
                self._emit("failed", stage="designer", reason=str(exc))
                return {"attempts": attempt, "status": "failed", "message": f"Designer failed: {exc}"}
            return {"candidate": candidate, "attempts": attempt}

        def validate(state: WorkflowState) -> dict[str, Any]:
            self._emit("validation_started", attempt=state["attempts"])
            try:
                spec = parse_game_spec_v1(state.get("candidate"))
                solved = solve_game(spec)
                if not solved.winnable:
                    error = getattr(solved, "closest_distance", getattr(solved, "error", None))
                    raise ValueError(f"declared solution is not winnable (solver error: {error})")
            except Exception as exc:  # invalid/refused review triggers bounded repair
                self._emit("validation_failed", attempt=state["attempts"], reason=str(exc))
                if state["attempts"] >= self.max_attempts:
                    return {"status": "failed", "message": f"No valid game after {state['attempts']} attempts: {exc}"}
                return {"feedback": str(exc)}
            self._emit("validation_completed", game_type=spec.game_type)
            return {"spec": spec, "feedback": ""}

        def review(state: WorkflowState) -> dict[str, Any]:
            self._emit("reviewer_started", attempt=state["attempts"])
            try:
                raw = self.reviewer.invoke([
                    SystemMessage(content=REVIEWER_PROMPT),
                    HumanMessage(content=(
                        f"Brief: {state['decision'].design_brief}\n"
                        f"Candidate: {state['spec'].model_dump_json()}\n"
                        "Deterministic solver: winnable"
                    )),
                ])
                decision = self._coerce(raw, GameReviewV1)
            except (ValidationError, ValueError, TypeError) as exc:
                decision = GameReviewV1(approved=False, feedback=f"Invalid reviewer output: {exc}")
            self._emit("reviewer_completed", approved=decision.approved)
            if decision.approved:
                return {"review": decision, "status": "ready", "message": "Game is ready."}
            if state["attempts"] >= self.max_attempts:
                return {"review": decision, "status": "failed", "message": f"Review failed after {state['attempts']} attempts: {decision.feedback}"}
            return {"review": decision, "feedback": decision.feedback or "Improve fidelity to the brief."}

        graph.add_node("plan", plan)
        graph.add_node("design", design)
        graph.add_node("validate", validate)
        graph.add_node("review", review)
        graph.add_edge(START, "plan")
        graph.add_conditional_edges("plan", lambda s: "design" if "decision" in s and s.get("status") is None else END)
        graph.add_conditional_edges("design", lambda s: "validate" if s.get("status") != "failed" else END)
        graph.add_conditional_edges("validate", lambda s: "review" if "spec" in s and not s.get("feedback") else (END if s.get("status") == "failed" else "design"))
        graph.add_conditional_edges("review", lambda s: END if s.get("status") in {"ready", "failed"} else "design")
        return graph.compile(checkpointer=self.checkpointer)

    def invoke(self, request: str, *, thread_id: str | None = None) -> WorkflowState:
        """Generate one game or return a clarification/failure outcome."""
        if not request.strip():
            return {"request": request, "status": "needs_more_info", "message": "What would you like the learner to practise?"}
        config = {"configurable": {"thread_id": thread_id}} if thread_id else None
        return self.graph.invoke({"request": request.strip()}, config=config)


def create_openai_structured_workflow(
    *,
    planner_model: str,
    designer_model: str,
    reviewer_model: str,
    max_attempts: int = 3,
    progress: ProgressCallback | None = None,
    api_key: str | None = None,
    checkpointer: Any | None = None,
) -> StructuredGameWorkflow:
    """Production convenience factory; tests should inject fake model objects."""
    return StructuredGameWorkflow(
        planner_llm=ChatOpenAI(model=planner_model, api_key=api_key),
        designer_llm=ChatOpenAI(model=designer_model, api_key=api_key),
        reviewer_llm=ChatOpenAI(model=reviewer_model, api_key=api_key),
        max_attempts=max_attempts,
        progress=progress,
        checkpointer=checkpointer,
    )
