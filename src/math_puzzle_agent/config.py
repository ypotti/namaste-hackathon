"""
config.py — Central hyperparameter configuration for the Math Puzzle Agent workflow.

All tunable knobs live here so you can test different combinations without
touching workflow.py, prompts.py, or the .env file.

Usage:
    from .config import WorkflowConfig
    cfg = WorkflowConfig()          # uses env vars / defaults
    cfg = WorkflowConfig(           # explicit override for a test run
        generator_model="gpt-4o",
        generator_temperature=0.5,
        max_review_attempts=5,
    )
"""

from __future__ import annotations

import os
import random
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class WorkflowConfig:
    # ─────────────────────────────────────────────────────────────────
    # 1. MODEL SELECTION
    #    Which OpenAI model each agent node uses.
    #    Reasoning models (o1, o3, gpt-5*) ignore temperature automatically.
    #    Swap to cheaper models (gpt-4o-mini) to cut costs during bulk testing.
    # ─────────────────────────────────────────────────────────────────
    planner_model: str = field(
        default_factory=lambda: (
            os.getenv("PLANNER_MODEL")
            or os.getenv("OPENAI_MODEL")
            or "gpt-5.5"
        )
    )
    reviewer_model: str = field(
        default_factory=lambda: (
            os.getenv("REVIEWER_MODEL")
            or os.getenv("OPENAI_MODEL")
            or "gpt-5.5-mini"
        )
    )
    generator_model: str = field(
        default_factory=lambda: (
            os.getenv("GENERATOR_MODEL")
            or os.getenv("OPENAI_MODEL")
            or "gpt-5.5-mini"
        )
    )

    # ─────────────────────────────────────────────────────────────────
    # 2. TEMPERATURE
    #    Controls randomness / creativity for each node independently.
    #    0.0  → fully deterministic, best for reproducible tests
    #    0.3  → slight variety while staying coherent
    #    0.7+ → more creative but less predictable HTML output
    #    Note: ignored automatically for reasoning models (o1/o3/o4/gpt-5*).
    # ─────────────────────────────────────────────────────────────────
    planner_temperature: float = 0.0
    reviewer_temperature: float = 0.0
    generator_temperature: float = 0.0

    # ─────────────────────────────────────────────────────────────────
    # 3. REVIEW / RETRY LOOP
    #    max_review_attempts: max times the generator can be called before
    #    the workflow force-exits the review loop and writes whatever it has.
    #    Higher = better quality ceiling, higher cost + latency.
    #    Recommended range: 1–5
    # ─────────────────────────────────────────────────────────────────
    max_review_attempts: int = 3

    # ─────────────────────────────────────────────────────────────────
    # 4. PUZZLE SPEC DEFAULTS
    #    default_tolerance: fallback accepted_tolerance injected into
    #    the planner prompt when the user doesn't specify one.
    #    0.05 → tight (forces exact answer)
    #    0.15 → lenient (current default; forgives rounding)
    #    0.25 → very forgiving (good for young learners)
    # ─────────────────────────────────────────────────────────────────
    default_tolerance: float = 0.15

    # ─────────────────────────────────────────────────────────────────
    # 5. OUTPUT
    #    output_dir: where the generated HTML file is written.
    #    Change per run to keep multiple test outputs side-by-side.
    # ─────────────────────────────────────────────────────────────────
    output_dir: Path = field(default_factory=lambda: Path.cwd() / "generated")

    # ─────────────────────────────────────────────────────────────────
    # 6. CANVAS DIMENSIONS
    #    These are embedded in the generator prompt.
    #    canvas_width / canvas_height: pixel dimensions of the p5.js canvas.
    #    Standard: 900x520. Try 800x450 for a more compact layout.
    # ─────────────────────────────────────────────────────────────────
    canvas_width: int = 900
    canvas_height: int = 520

    # ─────────────────────────────────────────────────────────────────
    # 7. P5.JS CDN URL
    #    Pin to a specific version here so generator output stays stable
    #    across runs. Change to test newer p5.js releases.
    # ─────────────────────────────────────────────────────────────────
    p5_cdn_url: str = "https://cdn.jsdelivr.net/npm/p5@1.11.3/lib/p5.min.js"

    # ─────────────────────────────────────────────────────────────────
    # 8. THREAD / SESSION
    #    thread_id: LangGraph checkpointer thread. Use a fixed string for
    #    reproducible multi-turn tests; use None to auto-generate a UUID.
    # ─────────────────────────────────────────────────────────────────
    thread_id: str | None = field(
        default_factory=lambda: os.getenv("PUZZLE_THREAD_ID", "default-puzzle-chat")
    )

    # ─────────────────────────────────────────────────────────────────
    # 9. SQLITE CHECKPOINT DB PATH
    #    Separate DB paths per experiment prevent state bleed between runs.
    # ─────────────────────────────────────────────────────────────────
    checkpoint_db_path: Path = field(
        default_factory=lambda: Path.cwd() / "puzzle_agent.sqlite"
    )

    # ─────────────────────────────────────────────────────────────────
    # 10. VISUAL REVIEW VIA HEADLESS BROWSER
    #     screenshot_enabled: when True, each reviewer pass renders the
    #     generated HTML in a headless Chromium browser, captures a
    #     full-page screenshot, and sends it to the vision model so the
    #     reviewer can spot layout/styling bugs that are invisible in raw
    #     HTML alone.
    #
    #     reviewer_vision_model: the OpenAI model used for the visual
    #     pre-pass. Must support vision (image) inputs. gpt-4o is the
    #     recommended default; gpt-4o-mini works for cost-sensitive runs.
    #
    #     screenshot_dir: folder where all captured screenshots are saved.
    #     Each file is named  review_attempt_<N>_<timestamp>.png  so you
    #     can compare across retry iterations.
    #
    #     screenshot_save: when True (default), screenshots are kept on
    #     disk after the run. Set to False to capture-and-discard (the
    #     image is still sent to the model; it is just not persisted).
    # ─────────────────────────────────────────────────────────────────
    screenshot_enabled: bool = field(
        default_factory=lambda: os.getenv("SCREENSHOT_ENABLED", "true").lower() == "true"
    )
    reviewer_vision_model: str = field(
        default_factory=lambda: (
            os.getenv("REVIEWER_VISION_MODEL")
            or os.getenv("OPENAI_MODEL")
            or "gpt-4o"
        )
    )
    screenshot_dir: Path = field(
        default_factory=lambda: Path.cwd() / "screenshots"
    )
    screenshot_save: bool = field(
        default_factory=lambda: os.getenv("SCREENSHOT_SAVE", "true").lower() == "true"
    )

    # ─────────────────────────────────────────────────────────────────
    # 11. INPUT GUARDRAIL
    #     guardrail_enabled: when True, the input guardrail will filter
    #     out prompts that are off-topic, harmful, jailbreaks, or prompt stealing.
    #     guardrail_threshold: similarity threshold for blocking.
    #     guardrail_embedding_model: embedding model to use.
    # ─────────────────────────────────────────────────────────────────
    guardrail_enabled: bool = field(
        default_factory=lambda: os.getenv("GUARDRAIL_ENABLED", "true").lower() == "true"
    )
    guardrail_threshold: float = field(
        default_factory=lambda: float(os.getenv("GUARDRAIL_THRESHOLD", "0.35"))
    )
    guardrail_embedding_model: str = field(
        default_factory=lambda: os.getenv("GUARDRAIL_EMBEDDING_MODEL", "text-embedding-3-small")
    )

    # ─────────────────────────────────────────────────────────────────
    # 12. SESSION RUN ID
    #     A 4-digit random number generated once per process startup.
    #     Combined with the thread_id it makes every screenshot filename
    #     unique across runs even when the thread_id is reused.
    #     Format used in screenshot names:
    #       review_attempt_{n}_{thread_id}_{session_run_id}_{timestamp}.png
    # ─────────────────────────────────────────────────────────────────
    session_run_id: str = field(
        default_factory=lambda: f"{random.randint(0, 9999):04d}"
    )

    def __post_init__(self) -> None:
        """Coerce string paths to Path objects (handy when loading from env/dict)."""
        if not isinstance(self.output_dir, Path):
            self.output_dir = Path(self.output_dir)
        if not isinstance(self.checkpoint_db_path, Path):
            self.checkpoint_db_path = Path(self.checkpoint_db_path)
        if not isinstance(self.screenshot_dir, Path):
            self.screenshot_dir = Path(self.screenshot_dir)

    def summary(self) -> str:
        """Return a human-readable summary of the active config for logging."""
        return (
            f"WorkflowConfig(\n"
            f"  planner   : {self.planner_model}  (temp={self.planner_temperature})\n"
            f"  generator : {self.generator_model}  (temp={self.generator_temperature})\n"
            f"  reviewer  : {self.reviewer_model}  (temp={self.reviewer_temperature})\n"
            f"  max_review_attempts : {self.max_review_attempts}\n"
            f"  default_tolerance   : {self.default_tolerance}\n"
            f"  canvas              : {self.canvas_width}x{self.canvas_height}\n"
            f"  p5_cdn_url          : {self.p5_cdn_url}\n"
            f"  output_dir          : {self.output_dir}\n"
            f"  checkpoint_db       : {self.checkpoint_db_path}\n"
            f"  thread_id           : {self.thread_id}\n"
            f"  screenshot_enabled  : {self.screenshot_enabled}\n"
            f"  reviewer_vision_model: {self.reviewer_vision_model}\n"
            f"  screenshot_dir      : {self.screenshot_dir}\n"
            f"  screenshot_save     : {self.screenshot_save}\n"
            f"  guardrail_enabled   : {self.guardrail_enabled}\n"
            f"  guardrail_threshold : {self.guardrail_threshold}\n"
            f"  guardrail_embedding_model: {self.guardrail_embedding_model}\n"
            f"  session_run_id      : {self.session_run_id}\n"
            f")"
        )
