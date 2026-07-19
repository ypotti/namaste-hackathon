"""Canonical verified fixture shared by examples and contract tests."""

from __future__ import annotations

import math

from .schemas import (BalanceTorqueSpecV1, FallingObjectSpecV1, FractionGroupingSpecV1,
    GraphMatchSpecV1, MomentumCollisionSpecV1, ProjectileTargetSpecV1)


_ANGLE = 48
_POWER = 76
_FLIGHT_TIME = 2.75
_GRAVITY = 9.8
_SPEED = _POWER * 3.32

CANONICAL_PROJECTILE_GAME = ProjectileTargetSpecV1.model_validate(
    {
        "title": "Arc Runner",
        "concept": "Projectile Motion",
        "eyebrow": "MOTION · GRAVITY",
        "instructions": "Balance horizontal speed and airtime to cross the elevated target.",
        "difficulty": "intermediate",
        "scene": {
            "theme": "stadium",
            "player_object": "probe",
            "target_object": "energy_gate",
            "effect": "orange_trail",
        },
        "controls": {},
        "physics": {
            "gravity": _GRAVITY,
            "target_x": round(102 + _SPEED * math.cos(math.radians(_ANGLE)) * _FLIGHT_TIME),
            "target_y": round(
                366
                - (
                    _SPEED * math.sin(math.radians(_ANGLE)) * _FLIGHT_TIME
                    - 0.5 * _GRAVITY * 10 * _FLIGHT_TIME**2
                )
            ),
        },
        "solution": {"angle": _ANGLE, "power": _POWER},
        "learning": {
            "principle": "You shaped a projectile arc",
            "explanation": "Horizontal velocity carried the probe forward while gravity bent its path into a parabola.",
            "hint": "Raise the angle for more airtime, or add thrust for more range.",
        },
    }
)

_COPY = {"title": "Precision Challenge", "concept": "Applied mathematics", "eyebrow": "TEST · LEARN",
         "instructions": "Adjust the control until the measured result matches the target.",
         "difficulty": "starter", "learning": {"principle": "Models predict outcomes",
         "explanation": "A mathematical relationship connects the controls to the observed result.",
         "hint": "Compare your result with the target, then adjust one control."}}

CANONICAL_FALLING_GAME = FallingObjectSpecV1.model_validate({**_COPY, "game_type": "falling_object", "scene": "tower",
    "physics": {"gravity": 10.0, "target_time": 2.0}, "solution_height": 200})
CANONICAL_BALANCE_GAME = BalanceTorqueSpecV1.model_validate({**_COPY, "game_type": "balance_torque", "scene": "workshop",
    "physics": {"left_weight": 20.0, "left_distance": 3.0, "right_weight": 15.0}, "solution_right_distance": 4.0})
CANONICAL_MOMENTUM_GAME = MomentumCollisionSpecV1.model_validate({**_COPY, "game_type": "momentum_collision", "scene": "track",
    "physics": {"player_mass": 10.0, "other_mass": 10.0, "other_velocity": 0.0, "target_velocity": 5.0}, "solution_player_velocity": 10.0})
CANONICAL_FRACTION_GAME = FractionGroupingSpecV1.model_validate({**_COPY, "game_type": "fraction_grouping", "scene": "garden",
    "total_items": 12, "numerator": 2, "denominator": 3, "solution_selected_count": 8})
CANONICAL_GRAPH_GAME = GraphMatchSpecV1.model_validate({**_COPY, "game_type": "graph_match", "scene": "coordinate_grid",
    "target_slope": 2.0, "target_intercept": -3.0, "solution_slope": 2.0, "solution_intercept": -3.0})

CANONICAL_GAMES = (CANONICAL_PROJECTILE_GAME, CANONICAL_FALLING_GAME, CANONICAL_BALANCE_GAME,
                   CANONICAL_MOMENTUM_GAME, CANONICAL_FRACTION_GAME, CANONICAL_GRAPH_GAME)
