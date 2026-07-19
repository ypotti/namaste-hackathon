"""Canonical, versioned contracts for trusted frontend game renderers."""

from __future__ import annotations

from typing import Annotated, Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, model_validator


ShortText = Annotated[str, Field(min_length=1, max_length=120)]
BodyText = Annotated[str, Field(min_length=1, max_length=360)]


class ContractModel(BaseModel):
    """Base for contracts where unknown model-generated fields are unsafe."""

    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)


class ProjectileSceneV1(ContractModel):
    theme: Literal["lab", "moon", "stadium", "orbit", "cliff"]
    player_object: Literal["probe", "ball"] = "probe"
    target_object: Literal[
        "energy_gate", "hoop", "capture_field", "checkpoint", "survey_ring"
    ] = "energy_gate"
    effect: Literal["orange_trail", "comet_trail", "motion_dots"] = "orange_trail"


class AngleControlV1(ContractModel):
    id: Literal["angle"] = "angle"
    label: ShortText = "Launch angle"
    min: Literal[20] = 20
    max: Literal[65] = 65
    step: Literal[1] = 1
    default: Annotated[int, Field(ge=20, le=65)] = 42
    unit: Literal["degrees"] = "degrees"


class ThrustControlV1(ContractModel):
    id: Literal["thrust"] = "thrust"
    label: ShortText = "Thrust"
    min: Literal[55] = 55
    max: Literal[100] = 100
    step: Literal[1] = 1
    default: Annotated[int, Field(ge=55, le=100)] = 76
    unit: Literal["percent"] = "percent"


class ProjectileControlsV1(ContractModel):
    angle: AngleControlV1 = Field(default_factory=AngleControlV1)
    thrust: ThrustControlV1 = Field(default_factory=ThrustControlV1)


class PointV1(ContractModel):
    x: Annotated[float, Field(allow_inf_nan=False)]
    y: Annotated[float, Field(allow_inf_nan=False)]


class ProjectilePhysicsV1(ContractModel):
    gravity: Annotated[float, Field(ge=4, le=16, allow_inf_nan=False)]
    target_x: Annotated[int, Field(ge=480, le=735)]
    target_y: Annotated[int, Field(ge=90, le=330)]
    launch_point: PointV1 = Field(
        default_factory=lambda: PointV1(x=102.0, y=366.0), frozen=True
    )
    thrust_scale: Literal[3.32] = 3.32
    target_tolerance: Literal[42] = 42
    timestep_seconds: Literal[0.025] = 0.025
    max_steps: Literal[320] = 320

    @model_validator(mode="after")
    def fixed_renderer_contract(self) -> "ProjectilePhysicsV1":
        if self.launch_point.x != 102 or self.launch_point.y != 366:
            raise ValueError("launch_point must be the renderer contract point (102, 366)")
        return self


class ProjectileSolutionV1(ContractModel):
    angle: Annotated[int, Field(ge=20, le=65)]
    power: Annotated[int, Field(ge=55, le=100)]


class LearningV1(ContractModel):
    principle: ShortText
    explanation: BodyText
    hint: BodyText


class ProjectileTargetSpecV1(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    game_type: Literal["projectile_target"] = "projectile_target"
    renderer_version: Literal["projectile-svg@1"] = "projectile-svg@1"
    solver_version: Literal["projectile@1"] = "projectile@1"
    title: ShortText
    concept: ShortText
    eyebrow: Annotated[str, Field(min_length=1, max_length=48)]
    instructions: BodyText
    difficulty: Literal["starter", "intermediate", "advanced"]
    scene: ProjectileSceneV1
    controls: ProjectileControlsV1
    physics: ProjectilePhysicsV1
    solution: ProjectileSolutionV1
    learning: LearningV1

    @model_validator(mode="after")
    def solution_matches_control_contract(self) -> "ProjectileTargetSpecV1":
        if not self.controls.angle.min <= self.solution.angle <= self.controls.angle.max:
            raise ValueError("solution angle is outside the angle control range")
        if not self.controls.thrust.min <= self.solution.power <= self.controls.thrust.max:
            raise ValueError("solution power is outside the thrust control range")
        return self


class FallingObjectPhysicsV1(ContractModel):
    gravity: Annotated[float, Field(ge=4, le=16, allow_inf_nan=False)]
    target_time: Annotated[float, Field(ge=0.5, le=4, allow_inf_nan=False)]
    time_tolerance: Annotated[float, Field(gt=0, le=0.25, allow_inf_nan=False)] = 0.08


class FallingObjectSpecV1(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    game_type: Literal["falling_object"] = "falling_object"
    renderer_version: Literal["falling-svg@1"] = "falling-svg@1"
    solver_version: Literal["falling@1"] = "falling@1"
    title: ShortText
    concept: ShortText
    eyebrow: Annotated[str, Field(min_length=1, max_length=48)]
    instructions: BodyText
    difficulty: Literal["starter", "intermediate", "advanced"]
    scene: Literal["lab", "tower", "moon"]
    physics: FallingObjectPhysicsV1
    solution_height: Annotated[int, Field(ge=20, le=800)]
    learning: LearningV1


class BalanceTorquePhysicsV1(ContractModel):
    left_weight: Annotated[float, Field(ge=1, le=100, allow_inf_nan=False)]
    left_distance: Annotated[float, Field(ge=0.5, le=10, allow_inf_nan=False)]
    right_weight: Annotated[float, Field(ge=1, le=100, allow_inf_nan=False)]
    torque_tolerance: Annotated[float, Field(gt=0, le=5, allow_inf_nan=False)] = 0.5


class BalanceTorqueSpecV1(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    game_type: Literal["balance_torque"] = "balance_torque"
    renderer_version: Literal["balance-svg@1"] = "balance-svg@1"
    solver_version: Literal["balance@1"] = "balance@1"
    title: ShortText
    concept: ShortText
    eyebrow: Annotated[str, Field(min_length=1, max_length=48)]
    instructions: BodyText
    difficulty: Literal["starter", "intermediate", "advanced"]
    scene: Literal["workshop", "playground", "lab"]
    physics: BalanceTorquePhysicsV1
    solution_right_distance: Annotated[float, Field(ge=0.5, le=10, allow_inf_nan=False)]
    learning: LearningV1


class MomentumPhysicsV1(ContractModel):
    player_mass: Annotated[float, Field(ge=1, le=100, allow_inf_nan=False)]
    other_mass: Annotated[float, Field(ge=1, le=100, allow_inf_nan=False)]
    other_velocity: Annotated[float, Field(ge=-30, le=30, allow_inf_nan=False)]
    target_velocity: Annotated[float, Field(ge=-30, le=30, allow_inf_nan=False)]
    velocity_tolerance: Annotated[float, Field(gt=0, le=1, allow_inf_nan=False)] = 0.1


class MomentumCollisionSpecV1(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    game_type: Literal["momentum_collision"] = "momentum_collision"
    renderer_version: Literal["collision-svg@1"] = "collision-svg@1"
    solver_version: Literal["momentum@1"] = "momentum@1"
    title: ShortText
    concept: ShortText
    eyebrow: Annotated[str, Field(min_length=1, max_length=48)]
    instructions: BodyText
    difficulty: Literal["starter", "intermediate", "advanced"]
    scene: Literal["track", "space", "lab"]
    physics: MomentumPhysicsV1
    solution_player_velocity: Annotated[float, Field(ge=-30, le=30, allow_inf_nan=False)]
    learning: LearningV1


class FractionGroupingSpecV1(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    game_type: Literal["fraction_grouping"] = "fraction_grouping"
    renderer_version: Literal["fraction-svg@1"] = "fraction-svg@1"
    solver_version: Literal["fraction@1"] = "fraction@1"
    title: ShortText
    concept: ShortText
    eyebrow: Annotated[str, Field(min_length=1, max_length=48)]
    instructions: BodyText
    difficulty: Literal["starter", "intermediate", "advanced"]
    scene: Literal["garden", "bakery", "classroom"]
    total_items: Annotated[int, Field(ge=4, le=48)]
    numerator: Annotated[int, Field(ge=1, le=12)]
    denominator: Annotated[int, Field(ge=2, le=12)]
    solution_selected_count: Annotated[int, Field(ge=1, le=48)]
    learning: LearningV1

    @model_validator(mode="after")
    def valid_fraction(self) -> "FractionGroupingSpecV1":
        if self.numerator >= self.denominator:
            raise ValueError("numerator must be smaller than denominator")
        if self.total_items % self.denominator:
            raise ValueError("total_items must be divisible by denominator")
        return self


class GraphMatchSpecV1(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    game_type: Literal["graph_match"] = "graph_match"
    renderer_version: Literal["graph-svg@1"] = "graph-svg@1"
    solver_version: Literal["linear-graph@1"] = "linear-graph@1"
    title: ShortText
    concept: ShortText
    eyebrow: Annotated[str, Field(min_length=1, max_length=48)]
    instructions: BodyText
    difficulty: Literal["starter", "intermediate", "advanced"]
    scene: Literal["coordinate_grid", "motion_graph", "lab_chart"]
    target_slope: Annotated[float, Field(ge=-10, le=10, allow_inf_nan=False)]
    target_intercept: Annotated[float, Field(ge=-20, le=20, allow_inf_nan=False)]
    solution_slope: Annotated[float, Field(ge=-10, le=10, allow_inf_nan=False)]
    solution_intercept: Annotated[float, Field(ge=-20, le=20, allow_inf_nan=False)]
    tolerance: Annotated[float, Field(gt=0, le=0.5, allow_inf_nan=False)] = 0.05
    learning: LearningV1


# ``game_type`` is a required literal discriminator. When a second V1 mechanic
# lands this alias becomes ``Annotated[ProjectileTargetSpecV1 | ..., Field(
# discriminator="game_type")]`` without changing the public parsing boundary.
# A one-member Union is collapsed by Python/Pydantic, so using the concrete
# subtype today avoids a misleading or invalid discriminator declaration.
GameSpecV1: TypeAlias = Annotated[
    ProjectileTargetSpecV1 | FallingObjectSpecV1 | BalanceTorqueSpecV1
    | MomentumCollisionSpecV1 | FractionGroupingSpecV1 | GraphMatchSpecV1,
    Field(discriminator="game_type"),
]
GAME_SPEC_V1_ADAPTER = TypeAdapter(GameSpecV1)


def parse_game_spec_v1(value: object) -> GameSpecV1:
    """Strictly validate an untrusted JSON-like game specification."""

    return GAME_SPEC_V1_ADAPTER.validate_python(value, strict=True)
