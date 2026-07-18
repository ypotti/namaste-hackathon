from math_puzzle_agent.schemas import PlannerDecision, ReviewerDecision
from math_puzzle_agent.workflow import (
    get_llm,
    route_after_planning,
    route_after_review,
    strip_code_fence,
)


def test_route_uses_planner_status():
    assert route_after_planning({"decision": PlannerDecision(status="need_more_info")}) == "ask_user"
    assert route_after_planning({"decision": PlannerDecision(status="ready")}) == "generator"


def test_strips_accidental_html_fence():
    assert strip_code_fence("```html\n<!doctype html><html></html>\n```") == "<!doctype html><html></html>"


def test_get_llm_temperature(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "mock-key")
    
    # Standard models default to temperature=0
    llm_standard = get_llm("gpt-4o")
    assert llm_standard.temperature == 0.0
    
    # Reasoning models or GPT-5 models should not have temperature set to 0.0
    llm_reasoning_o1 = get_llm("o1-mini")
    assert llm_reasoning_o1.temperature != 0.0
    
    llm_reasoning_o3 = get_llm("o3-mini")
    assert llm_reasoning_o3.temperature != 0.0
    
    llm_reasoning_gpt5 = get_llm("gpt-5.5")
    assert llm_reasoning_gpt5.temperature != 0.0


def test_route_after_review():
    # If approved, write file and finish
    assert route_after_review({
        "reviewer_decision": ReviewerDecision(approved=True, feedback=""),
        "generation_attempts": 1,
    }) == "write_file_and_finish"

    # If not approved and generation_attempts < 3, retry generator
    assert route_after_review({
        "reviewer_decision": ReviewerDecision(approved=False, feedback="Fix css classes"),
        "generation_attempts": 1,
    }) == "generator"

    # If not approved but attempts reach 3, fallback to write_file_and_finish
    assert route_after_review({
        "reviewer_decision": ReviewerDecision(approved=False, feedback="Fix css classes"),
        "generation_attempts": 3,
    }) == "write_file_and_finish"
