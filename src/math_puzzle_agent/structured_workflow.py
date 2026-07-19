"""LangGraph workflow that produces trusted, solver-proven game specifications.

LLMs are injected, making this module usable by FastAPI and deterministic in tests.
It delegates to the proven legacy HTML-generating graph, which operates on PuzzleSpec.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Literal, Protocol, TypedDict

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from .config import WorkflowConfig
from .schemas import PuzzleSpec, PlannerDecision
from .workflow import build_graph as _legacy_build_graph

ProgressCallback = Callable[[str, dict[str, Any]], None]


class StructuredModel(Protocol):
    def invoke(self, input: Any, **kwargs: Any) -> Any: ...


class StructuredCapableModel(Protocol):
    def with_structured_output(self, schema: type[Any]) -> StructuredModel: ...


class WorkflowState(TypedDict, total=False):
    request: str
    decision: PlannerDecision
    spec: PuzzleSpec
    candidate: object
    attempts: int
    feedback: str
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
        vision_llm: StructuredModel | None = None,
        cfg: WorkflowConfig | None = None,
        max_attempts: int = 3,
        progress: ProgressCallback | None = None,
        checkpointer: Any | None = None,
    ) -> None:
        self.cfg = cfg or WorkflowConfig()
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least one")
        self.planner_llm = planner_llm
        self.designer_llm = designer_llm
        self.reviewer_llm = reviewer_llm
        self.vision_llm = vision_llm
        self.max_attempts = max_attempts
        self.progress = progress or (lambda _event, _details: None)
        self.checkpointer = checkpointer
        self.graph = self._build_graph()

    def _build_graph(self):
        """Delegate to the proven legacy HTML-generating graph."""
        return _legacy_build_graph(
            self.cfg,
            checkpointer=self.checkpointer,
            planner_llm=self.planner_llm,
            generator_llm=self.designer_llm,
            reviewer_llm=self.reviewer_llm,
            vision_llm=self.vision_llm or self.reviewer_llm,
        )

    def invoke(self, request: str, *, thread_id: str | None = None) -> WorkflowState:
        """Generate one game or return a clarification/failure outcome."""
        if not request.strip():
            return {"request": request, "status": "needs_more_info", "message": "What would you like the learner to practise?"}
        if thread_id:
            self.cfg.thread_id = thread_id
        config = {"configurable": {"thread_id": thread_id}} if thread_id else None
        
        result = self.graph.invoke({"messages": [HumanMessage(content=request.strip())]}, config=config)
        
        from math_puzzle_agent.services.structured_generation import _normalise_result
        return _normalise_result(result)


def create_openai_structured_workflow(
    *,
    planner_model: str,
    designer_model: str,
    reviewer_model: str,
    reviewer_vision_model: str | None = None,
    cfg: WorkflowConfig | None = None,
    max_attempts: int = 3,
    progress: ProgressCallback | None = None,
    api_key: str | None = None,
    checkpointer: Any | None = None,
) -> StructuredGameWorkflow:
    """Production convenience factory; tests should inject fake model objects."""
    vision_llm = None
    if reviewer_vision_model:
        vision_llm = ChatOpenAI(model=reviewer_vision_model, api_key=api_key)
    return StructuredGameWorkflow(
        planner_llm=ChatOpenAI(model=planner_model, api_key=api_key),
        designer_llm=ChatOpenAI(model=designer_model, api_key=api_key),
        reviewer_llm=ChatOpenAI(model=reviewer_model, api_key=api_key),
        vision_llm=vision_llm,
        cfg=cfg,
        max_attempts=max_attempts,
        progress=progress,
        checkpointer=checkpointer,
    )
