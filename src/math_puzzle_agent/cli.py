from __future__ import annotations

import logging
import os
import sqlite3
import uuid

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver

from .config import WorkflowConfig
from .workflow import build_graph


def _configure_logging() -> None:
    """
    Set up a clean, human-readable log format for the math_puzzle_agent package.

    Only our package logger is set to INFO — LangChain, OpenAI, httpx, and
    other third-party loggers stay at WARNING so they don't flood the console.
    """
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s  %(message)s",
            datefmt="%H:%M:%S",
        )
    )

    pkg_logger = logging.getLogger("math_puzzle_agent")
    pkg_logger.setLevel(logging.INFO)
    pkg_logger.addHandler(handler)
    pkg_logger.propagate = False  # don't double-print if root logger has handlers

    # Keep noisy third-party libraries quiet
    for noisy in ("httpx", "httpcore", "openai", "langchain", "langgraph"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def main() -> None:
    _configure_logging()
    load_dotenv()

    log = logging.getLogger("math_puzzle_agent.cli")

    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is missing. Copy .env.example to .env and add your key.")

    cfg = WorkflowConfig()
    log.info("Config loaded — planner: %s | generator: %s | reviewer: %s",
             cfg.planner_model, cfg.generator_model, cfg.reviewer_model)
    if cfg.screenshot_enabled:
        log.info("Visual review enabled — vision model: %s | save screenshots: %s",
                 cfg.reviewer_vision_model, cfg.screenshot_save)

    # Establish connection and build graph
    connection = sqlite3.connect(cfg.checkpoint_db_path, check_same_thread=False)
    graph = build_graph(cfg=cfg, checkpointer=SqliteSaver(connection))
    config = {"configurable": {"thread_id": cfg.thread_id}}

    print("\nMath Puzzle Agent — describe a puzzle.")
    print("Commands: /quit or /exit to exit, /new to start a fresh session.")
    print(f"Thread: {config['configurable']['thread_id']}\n")

    while True:
        try:
            current_thread = config["configurable"]["thread_id"]
            user_text = input(f"You ({current_thread}): ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if user_text.lower() in {"/quit", "/exit"}:
            break

        if user_text.lower() == "/new":
            new_id = f"puzzle-{uuid.uuid4().hex[:8]}"
            config["configurable"]["thread_id"] = new_id
            log.info("New session started — thread: %s", new_id)
            print(f"Started a new session! Thread: {new_id}\n")
            continue

        if not user_text:
            continue

        try:
            result = graph.invoke({"messages": [HumanMessage(content=user_text)]}, config=config)
            print(f"\nAgent: {result['messages'][-1].content}\n")
        except Exception as e:
            log.error("Workflow error: %s", e)
            print(f"\nError: {e}\n")


if __name__ == "__main__":
    main()
