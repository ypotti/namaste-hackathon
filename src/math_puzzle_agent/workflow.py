from __future__ import annotations

from pathlib import Path
from typing import Annotated, Literal, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

from .prompts import GENERATOR_PROMPT, PLANNER_PROMPT, REVIEWER_PROMPT
from .schemas import PlannerDecision, PuzzleSpec, ReviewerDecision


class PuzzleState(TypedDict, total=False):
    messages: Annotated[list[BaseMessage], add_messages]
    decision: PlannerDecision
    reviewer_decision: ReviewerDecision
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


def get_llm(model_name: str) -> ChatOpenAI:
    """Instantiate ChatOpenAI. Omits temperature for reasoning/gpt-5 models."""
    if model_name.startswith(("o1", "o3", "gpt-5")):
        return ChatOpenAI(model=model_name)
    return ChatOpenAI(model=model_name, temperature=0)


def route_after_planning(state: PuzzleState) -> Literal["generator", "ask_user"]:
    return "generator" if state["decision"].status == "ready" else "ask_user"


def route_after_review(state: PuzzleState) -> Literal["generator", "write_file_and_finish"]:
    decision: ReviewerDecision | None = state.get("reviewer_decision")
    attempts = state.get("generation_attempts", 0)
    
    if decision and decision.approved:
        return "write_file_and_finish"
        
    if attempts >= 3:  # Safeguard to prevent infinite review/generation loops
        return "write_file_and_finish"
        
    return "generator"


def build_graph(
    planner_model: str,
    reviewer_model: str,
    generator_model: str,
    output_dir: Path,
    checkpointer=None,
):
    """Build the workflow. Pass a LangGraph checkpointer for multi-turn memory."""
    planner_llm = get_llm(planner_model)
    reviewer_llm = get_llm(reviewer_model)
    generator_llm = get_llm(generator_model)

    planner = planner_llm.with_structured_output(PlannerDecision)
    reviewer = reviewer_llm.with_structured_output(ReviewerDecision)
    output_dir.mkdir(parents=True, exist_ok=True)

    def plan(state: PuzzleState):
        decision = planner.invoke([SystemMessage(content=PLANNER_PROMPT), *state["messages"]])
        return {"decision": decision}

    def ask_user(state: PuzzleState):
        decision = state["decision"]
        question = decision.next_question or "What essential puzzle detail should I use?"
        return {"messages": [AIMessage(content=question)]}

    def generate(state: PuzzleState):
        spec: PuzzleSpec = state["decision"].puzzle_spec  # set when status is ready
        
        # Check if there is review feedback from a previous run in the loop
        reviewer_decision: ReviewerDecision | None = state.get("reviewer_decision")
        feedback_text = (
            reviewer_decision.feedback
            if (reviewer_decision and not reviewer_decision.approved)
            else None
        )

        messages = [
            SystemMessage(content=GENERATOR_PROMPT),
            HumanMessage(content=spec.model_dump_json(indent=2)),
        ]

        if feedback_text:
            messages.append(
                HumanMessage(
                    content=f"The previous generation had the following issues. Please correct them:\n{feedback_text}"
                )
            )

        html = strip_code_fence(generator_llm.invoke(messages).content)
        attempts = state.get("generation_attempts", 0) + 1
        
        return {
            "generated_html": html,
            "generation_attempts": attempts,
        }

    def review(state: PuzzleState):
        spec: PuzzleSpec = state["decision"].puzzle_spec
        html = state.get("generated_html", "")
        
        prompt_content = (
            f"Puzzle Specification:\n{spec.model_dump_json(indent=2)}\n\n"
            f"Generated HTML:\n{html}"
        )

        decision = reviewer.invoke([
            SystemMessage(content=REVIEWER_PROMPT),
            HumanMessage(content=prompt_content),
        ])
        return {"reviewer_decision": decision}

    def write_file_and_finish(state: PuzzleState):
        html = state.get("generated_html", "").strip()
        
        # Robust basic validation check
        if not (html.lower().startswith("<!doctype html") or html.lower().startswith("<html")):
            raise ValueError("Generator did not return a complete HTML document.")
            
        path = output_dir / "math_puzzle.html"
        path.write_text(html, encoding="utf-8")
        file_url = f"file://{path.resolve()}"
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
    graph.add_conditional_edges("reviewer", route_after_review)
    graph.add_edge("ask_user", END)
    graph.add_edge("write_file_and_finish", END)

    return graph.compile(checkpointer=checkpointer)
