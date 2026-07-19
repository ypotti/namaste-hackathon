"""Versioned game contracts and deterministic verification."""

from .fixtures import (CANONICAL_BALANCE_GAME, CANONICAL_FALLING_GAME, CANONICAL_FRACTION_GAME,
    CANONICAL_GAMES, CANONICAL_GRAPH_GAME, CANONICAL_MOMENTUM_GAME, CANONICAL_PROJECTILE_GAME)
from .registry import solve_game, verify_game
from .schemas import (
    GameSpecV1,
    ProjectileTargetSpecV1,
    BalanceTorqueSpecV1, FallingObjectSpecV1, FractionGroupingSpecV1, GraphMatchSpecV1, MomentumCollisionSpecV1,
    parse_game_spec_v1,
)
from .solvers import (ProjectileSolverResult, ScalarSolverResult, simulate_balance, simulate_falling,
    simulate_fraction, simulate_graph, simulate_momentum, simulate_projectile)

__all__ = [
    "CANONICAL_PROJECTILE_GAME",
    "CANONICAL_BALANCE_GAME", "CANONICAL_FALLING_GAME", "CANONICAL_FRACTION_GAME", "CANONICAL_GAMES", "CANONICAL_GRAPH_GAME", "CANONICAL_MOMENTUM_GAME",
    "GameSpecV1",
    "ProjectileSolverResult",
    "ProjectileTargetSpecV1",
    "BalanceTorqueSpecV1", "FallingObjectSpecV1", "FractionGroupingSpecV1", "GraphMatchSpecV1", "MomentumCollisionSpecV1", "ScalarSolverResult",
    "parse_game_spec_v1",
    "simulate_projectile",
    "simulate_balance", "simulate_falling", "simulate_fraction", "simulate_graph", "simulate_momentum",
    "solve_game",
    "verify_game",
]
