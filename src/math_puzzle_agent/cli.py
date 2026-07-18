from __future__ import annotations

import os
import sqlite3
import uuid
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver

from .workflow import build_graph


def main() -> None:
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is missing. Copy .env.example to .env and add your key.")

    root = Path.cwd()
    
    # Read model configurations with fallbacks
    fallback_model = os.getenv("OPENAI_MODEL")
    planner_model = os.getenv("PLANNER_MODEL") or fallback_model or "gpt-5.5"
    reviewer_model = os.getenv("REVIEWER_MODEL") or fallback_model or "gpt-5.5-mini"
    generator_model = os.getenv("GENERATOR_MODEL") or fallback_model or "gpt-5.5-mini"

    thread_id = os.getenv("PUZZLE_THREAD_ID", "default-puzzle-chat")
    
    # Establish connection and build graph
    connection = sqlite3.connect(root / "puzzle_agent.sqlite", check_same_thread=False)
    graph = build_graph(
        planner_model=planner_model,
        reviewer_model=reviewer_model,
        generator_model=generator_model,
        output_dir=root / "generated",
        checkpointer=SqliteSaver(connection),
    )
    config = {"configurable": {"thread_id": thread_id}}

    print("Math Puzzle Agent — describe a puzzle.")
    print("Commands: /quit or /exit to exit, /new to start a brand new puzzle chat session.")
    print(f"Current Thread ID: {config['configurable']['thread_id']}")
    
    while True:
        try:
            current_thread = config["configurable"]["thread_id"]
            user_text = input(f"\nYou ({current_thread}): ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
            
        if user_text.lower() in {"/quit", "/exit"}:
            break
            
        if user_text.lower() == "/new":
            new_id = f"puzzle-{uuid.uuid4().hex[:8]}"
            config["configurable"]["thread_id"] = new_id
            print(f"Started a new session! New Thread ID: {new_id}")
            continue
            
        if not user_text:
            continue
            
        try:
            result = graph.invoke({"messages": [HumanMessage(content=user_text)]}, config=config)
            print(f"\nAgent: {result['messages'][-1].content}")
        except Exception as e:
            print(f"\nError: {e}")


if __name__ == "__main__":
    main()
