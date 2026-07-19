from __future__ import annotations

import pytest

from math_puzzle_agent.games import (
    CANONICAL_PROJECTILE_GAME,
    simulate_projectile,
    solve_game,
    verify_game,
)


def test_canonical_solution_is_verified() -> None:
    result = solve_game(CANONICAL_PROJECTILE_GAME)

    assert result.winnable is True
    assert result.closest_distance <= 42
    assert result.closest_step > 0


def test_solver_matches_demo_reference_values() -> None:
    result = simulate_projectile(CANONICAL_PROJECTILE_GAME)

    # These values lock Python verification to the demo's discrete 25 ms
    # screen-space simulation, rather than to an analytic approximation.
    assert result.closest_step == 110
    assert result.closest_point.x == pytest.approx(566.2963451)
    assert result.closest_point.y == pytest.approx(220.9091685)
    assert result.closest_distance == pytest.approx(0.3099529)


def test_bad_player_attempt_loses() -> None:
    result = simulate_projectile(CANONICAL_PROJECTILE_GAME, angle=20, power=55)

    assert result.winnable is False
    assert result.closest_distance > 42


def test_nearby_player_attempt_can_win_with_tolerance() -> None:
    result = simulate_projectile(CANONICAL_PROJECTILE_GAME, angle=47, power=76)

    assert result.winnable is True
    assert result.closest_distance <= CANONICAL_PROJECTILE_GAME.physics.target_tolerance


@pytest.mark.parametrize(
    ("angle", "power"),
    [(19, 76), (66, 76), (48, 54), (48, 101)],
)
def test_attempt_controls_are_bounded(angle: int, power: int) -> None:
    with pytest.raises(ValueError, match="outside the supported control range"):
        simulate_projectile(CANONICAL_PROJECTILE_GAME, angle=angle, power=power)


def test_verify_game_is_convenient_boolean_boundary() -> None:
    assert verify_game(CANONICAL_PROJECTILE_GAME) is True
