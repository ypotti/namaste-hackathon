"""Deterministic solvers for the bounded V1 game mechanics."""

from __future__ import annotations

import math
from typing import NamedTuple

from ..schemas import (
    BalanceTorqueSpecV1, FallingObjectSpecV1, FractionGroupingSpecV1,
    GraphMatchSpecV1, MomentumCollisionSpecV1,
)


class ScalarSolverResult(NamedTuple):
    winnable: bool
    actual: float
    target: float
    error: float


def simulate_falling(spec: FallingObjectSpecV1, *, height: int | None = None) -> ScalarSolverResult:
    value = spec.solution_height if height is None else height
    if not 20 <= value <= 800:
        raise ValueError("height is outside the supported control range")
    actual = math.sqrt(2 * value / (spec.physics.gravity * 10))
    error = abs(actual - spec.physics.target_time)
    return ScalarSolverResult(error <= spec.physics.time_tolerance, actual, spec.physics.target_time, error)


def simulate_balance(spec: BalanceTorqueSpecV1, *, right_distance: float | None = None) -> ScalarSolverResult:
    distance = spec.solution_right_distance if right_distance is None else right_distance
    if not 0.5 <= distance <= 10:
        raise ValueError("right_distance is outside the supported control range")
    target = spec.physics.left_weight * spec.physics.left_distance
    actual = spec.physics.right_weight * distance
    error = abs(actual - target)
    return ScalarSolverResult(error <= spec.physics.torque_tolerance, actual, target, error)


def simulate_momentum(spec: MomentumCollisionSpecV1, *, player_velocity: float | None = None) -> ScalarSolverResult:
    velocity = spec.solution_player_velocity if player_velocity is None else player_velocity
    if not -30 <= velocity <= 30:
        raise ValueError("player_velocity is outside the supported control range")
    p = spec.physics
    actual = (p.player_mass * velocity + p.other_mass * p.other_velocity) / (p.player_mass + p.other_mass)
    error = abs(actual - p.target_velocity)
    return ScalarSolverResult(error <= p.velocity_tolerance, actual, p.target_velocity, error)


def simulate_fraction(spec: FractionGroupingSpecV1, *, selected_count: int | None = None) -> ScalarSolverResult:
    count = spec.solution_selected_count if selected_count is None else selected_count
    if not 1 <= count <= spec.total_items:
        raise ValueError("selected_count is outside the supported control range")
    target = spec.total_items * spec.numerator / spec.denominator
    error = abs(count - target)
    return ScalarSolverResult(error == 0, float(count), target, error)


def simulate_graph(spec: GraphMatchSpecV1, *, slope: float | None = None, intercept: float | None = None) -> ScalarSolverResult:
    m = spec.solution_slope if slope is None else slope
    b = spec.solution_intercept if intercept is None else intercept
    if not -10 <= m <= 10 or not -20 <= b <= 20:
        raise ValueError("graph controls are outside the supported control range")
    error = max(abs(m - spec.target_slope), abs(b - spec.target_intercept))
    return ScalarSolverResult(error <= spec.tolerance, error, 0.0, error)
