from __future__ import annotations

import logging
import warnings
from typing import Annotated, Literal, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

from .browser import capture_screenshot, png_to_data_url
from .config import WorkflowConfig
from .prompts import get_generator_prompt, get_planner_prompt, get_reviewer_prompt, get_visual_review_prompt
from .schemas import PlannerDecision, PuzzleSpec, ReviewerDecision

log = logging.getLogger(__name__)


class PuzzleState(TypedDict, total=False):
    messages: Annotated[list[BaseMessage], add_messages]
    decision: PlannerDecision
    reviewer_decision: ReviewerDecision | None
    generated_html: str
    output_path: str
    generation_attempts: int


def strip_code_fence(text: str) -> str:
    """Recover HTML when a model accidentally wraps it in a Markdown fence."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else ""
        if cleaned.rstrip().endswith("```"):
            cleaned = cleaned.rstrip()[:-3]
    return cleaned.strip()


def get_llm(model_name: str, temperature: float = 0.0) -> ChatOpenAI:
    """Instantiate ChatOpenAI. Omits temperature for reasoning models that only
    support the default temperature (o1, o3, o4, gpt-5* series)."""
    reasoning_prefixes = ("o1", "o3", "o4", "gpt-5")
    if model_name.startswith(reasoning_prefixes):
        return ChatOpenAI(model=model_name)
    return ChatOpenAI(model=model_name, temperature=temperature)


def route_after_planning(state: PuzzleState) -> Literal["generator", "ask_user"]:
    return "generator" if state["decision"].status == "ready" else "ask_user"


def route_after_review(state: PuzzleState, max_attempts: int = 3) -> Literal["generator", "write_file_and_finish"]:
    decision: ReviewerDecision | None = state.get("reviewer_decision")
    attempts = state.get("generation_attempts", 0)

    if decision and decision.approved:
        return "write_file_and_finish"

    if attempts >= max_attempts:
        log.warning("Max review attempts (%d) reached — accepting current output", max_attempts)
        return "write_file_and_finish"

    return "generator"


def build_graph(cfg: WorkflowConfig, checkpointer=None):
    """Build the workflow. Pass a LangGraph checkpointer for multi-turn memory."""
    planner_llm = get_llm(cfg.planner_model, cfg.planner_temperature)
    reviewer_llm = get_llm(cfg.reviewer_model, cfg.reviewer_temperature)
    generator_llm = get_llm(cfg.generator_model, cfg.generator_temperature)
    # Vision LLM: plain (no structured output) — used for the screenshot pre-pass.
    # Must be a model that accepts image_url content blocks (e.g. gpt-4o, gpt-4.1).
    # Uses reviewer_temperature so it honours the same config knob.
    vision_llm = get_llm(cfg.reviewer_vision_model, cfg.reviewer_temperature)

    output_dir = cfg.output_dir

    planner = planner_llm.with_structured_output(PlannerDecision)
    reviewer = reviewer_llm.with_structured_output(ReviewerDecision)
    output_dir.mkdir(parents=True, exist_ok=True)

    def route_after_review_local(state: PuzzleState) -> Literal["generator", "write_file_and_finish"]:
        return route_after_review(state, max_attempts=cfg.max_review_attempts)

    def plan(state: PuzzleState):
        log.info("Planner  ▶  parsing intent...")
        decision = planner.invoke([SystemMessage(content=get_planner_prompt(cfg)), *state["messages"]])

        if decision.status == "ready":
            spec = decision.puzzle_spec
            log.info("Planner  ✔  spec ready — \"%s\" (%s)", spec.title, spec.math_concept)
            # Reset reviewer_decision and generation_attempts so a follow-up puzzle
            # in the same thread doesn't inherit state from the previous run.
            return {
                "decision": decision,
                "reviewer_decision": None,
                "generation_attempts": 0,
            }
        else:
            log.info("Planner  ?  needs more info — asking: %s", decision.next_question)
            return {"decision": decision}

    def ask_user(state: PuzzleState):
        decision = state["decision"]
        question = decision.next_question or "What essential puzzle detail should I use?"
        return {"messages": [AIMessage(content=question)]}

    def generate(state: PuzzleState):
        attempts = state.get("generation_attempts", 0) + 1
        reviewer_decision: ReviewerDecision | None = state.get("reviewer_decision")
        feedback_text = (
            reviewer_decision.feedback
            if (reviewer_decision and not reviewer_decision.approved)
            else None
        )

        if feedback_text:
            log.info("Generator ▶  attempt %d (fixing reviewer feedback)...", attempts)
        else:
            log.info("Generator ▶  attempt %d (first pass)...", attempts)

        spec: PuzzleSpec = state["decision"].puzzle_spec
        messages = [
            SystemMessage(content=get_generator_prompt(cfg)),
            HumanMessage(content=spec.model_dump_json(indent=2)),
        ]

        if feedback_text:
            messages.append(
                HumanMessage(
                    content=f"The previous generation had the following issues. Please correct them:\n{feedback_text}"
                )
            )

        html = strip_code_fence(generator_llm.invoke(messages).content)
        log.info("Generator ✔  HTML produced (%d chars)", len(html))

        return {
            "generated_html": html,
            "generation_attempts": attempts,
        }

    def review(state: PuzzleState):
        spec: PuzzleSpec = state["decision"].puzzle_spec
        html = state.get("generated_html", "")
        attempts = state.get("generation_attempts", 0)

        # ── Visual pre-pass ───────────────────────────────────────────────
        visual_observations: str = ""
        if cfg.screenshot_enabled:
            log.info("Reviewer  ▶  rendering screenshot (attempt %d)...", attempts)
            try:
                png_bytes, saved_path = capture_screenshot(html, cfg, attempts)
                data_url = png_to_data_url(png_bytes)

                if saved_path:
                    log.info("Reviewer  📷  screenshot saved → %s", saved_path)

                log.info("Reviewer  ▶  running visual analysis...")
                vision_message = HumanMessage(content=[
                    {
                        "type": "text",
                        "text": (
                            f"Puzzle Specification:\n{spec.model_dump_json(indent=2)}\n\n"
                            "The image below is a screenshot of the rendered HTML puzzle "
                            "in its idle state (no animation running yet). "
                            "Report visual defects per the checklist in your instructions."
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": data_url, "detail": "high"},
                    },
                ])
                visual_response = vision_llm.invoke([
                    SystemMessage(content=get_visual_review_prompt()),
                    vision_message,
                ])
                visual_observations = visual_response.content.strip()
                log.info("Reviewer  ✔  visual analysis complete")
            except Exception as exc:  # noqa: BLE001
                warnings.warn(
                    f"[reviewer] screenshot step failed, continuing without visual review: {exc}",
                    RuntimeWarning,
                    stacklevel=1,
                )
                log.warning("Reviewer  ⚠  screenshot failed, skipping visual pass: %s", exc)

        # ── Structured review pass ────────────────────────────────────────
        log.info("Reviewer  ▶  running structured review...")
        prompt_content = (
            f"Puzzle Specification:\n{spec.model_dump_json(indent=2)}\n\n"
            f"Generated HTML:\n{html}"
        )
        if visual_observations:
            prompt_content += (
                f"\n\n### Visual Review Observations (from rendered screenshot):\n"
                f"{visual_observations}"
            )

        decision = reviewer.invoke([
            SystemMessage(content=get_reviewer_prompt(cfg)),
            HumanMessage(content=prompt_content),
        ])

        if decision.approved:
            log.info("Reviewer  ✔  approved")
        else:
            # Show first 120 chars of feedback so it's scannable without flooding
            preview = decision.feedback[:120].replace("\n", " ")
            if len(decision.feedback) > 120:
                preview += "…"
            log.info("Reviewer  ✗  not approved — %s", preview)

        return {"reviewer_decision": decision}

    def write_file_and_finish(state: PuzzleState):
        html = state.get("generated_html", "").strip()

        # Robust basic validation check
        if not (html.lower().startswith("<!doctype html") or html.lower().startswith("<html")):
            raise ValueError("Generator did not return a complete HTML document.")

        # Derive a filename from the puzzle title: lowercase, spaces → underscores,
        # strip anything that isn't alphanumeric or an underscore, collapse runs.
        raw_title = state["decision"].puzzle_spec.title
        slug = raw_title.lower().strip()
        slug = "".join(c if c.isalnum() or c == " " else "" for c in slug)
        slug = "_".join(slug.split())          # collapse whitespace → underscores
        slug = slug[:60] or "math_puzzle"      # cap length; fallback if title was empty

        path = output_dir / f"{slug}.html"
        path.write_text(html, encoding="utf-8")
        file_url = f"file://{path.resolve()}"
        log.info("Done  ✔  puzzle written → %s", path)

        return {
            "output_path": str(path),
            "messages": [AIMessage(content=f"Your interactive puzzle is ready! Open it here: {file_url}")],
        }

    graph = StateGraph(PuzzleState)
    graph.add_node("planner", plan)
    graph.add_node("ask_user", ask_user)
    graph.add_node("generator", generate)
    graph.add_node("reviewer", review)
    graph.add_node("write_file_and_finish", write_file_and_finish)

    graph.add_edge(START, "planner")
    graph.add_conditional_edges("planner", route_after_planning)
    graph.add_edge("generator", "reviewer")
    graph.add_conditional_edges("reviewer", route_after_review_local)
    graph.add_edge("ask_user", END)
    graph.add_edge("write_file_and_finish", END)

    return graph.compile(checkpointer=checkpointer)
