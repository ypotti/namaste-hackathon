"""Solver dispatch kept exhaustive over the versioned game union."""

from __future__ import annotations

from typing import Never

from .schemas import (BalanceTorqueSpecV1, FallingObjectSpecV1, FractionGroupingSpecV1,
    GameSpecV1, GraphMatchSpecV1, MomentumCollisionSpecV1, ProjectileTargetSpecV1)
from .solvers import (ProjectileSolverResult, ScalarSolverResult, simulate_balance,
    simulate_falling, simulate_fraction, simulate_graph, simulate_momentum, simulate_projectile)


def _unreachable(value: Never) -> Never:
    raise TypeError(f"unsupported game spec: {type(value).__name__}")


def solve_game(spec: GameSpecV1) -> ProjectileSolverResult | ScalarSolverResult:
    if isinstance(spec, ProjectileTargetSpecV1):
        return simulate_projectile(spec)
    if isinstance(spec, FallingObjectSpecV1): return simulate_falling(spec)
    if isinstance(spec, BalanceTorqueSpecV1): return simulate_balance(spec)
    if isinstance(spec, MomentumCollisionSpecV1): return simulate_momentum(spec)
    if isinstance(spec, FractionGroupingSpecV1): return simulate_fraction(spec)
    if isinstance(spec, GraphMatchSpecV1): return simulate_graph(spec)
    return _unreachable(spec)


def verify_game(spec: GameSpecV1) -> bool:
    """Return whether the contract's hidden solution wins deterministically."""

    return solve_game(spec).winnable
