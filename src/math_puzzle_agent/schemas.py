from typing import Literal

from pydantic import BaseModel, Field


class KnownValue(BaseModel):
    name: str
    value: str


class PuzzleSpec(BaseModel):
    title: str
    math_concept: str
    scene_description: str
    question: str
    known_values: list[KnownValue] = Field(min_length=1)
    learner_answer_label: str
    correct_answer: float
    accepted_tolerance: float = Field(ge=0)
    answer_unit: str = ""
    formulas: list[str] = Field(min_length=1)
    solution_steps: list[str] = Field(min_length=2)
    hint: str
    animation_description: str
    assumptions: list[str] = Field(default_factory=list)


class PlannerDecision(BaseModel):
    status: Literal["need_more_info", "ready"]
    next_question: str | None = None
    missing_information: list[str] = Field(default_factory=list)
    puzzle_spec: PuzzleSpec | None = None


class ReviewerDecision(BaseModel):
    approved: bool
    feedback: str = Field(default="", description="Detailed feedback describing what to fix, or empty if approved.")

