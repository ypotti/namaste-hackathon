from __future__ import annotations

import pytest
from pydantic import ValidationError

from math_puzzle_agent.games import (
    CANONICAL_BALANCE_GAME, CANONICAL_FALLING_GAME, CANONICAL_FRACTION_GAME,
    CANONICAL_GAMES, CANONICAL_GRAPH_GAME, CANONICAL_MOMENTUM_GAME,
    parse_game_spec_v1, simulate_balance, simulate_falling, simulate_fraction,
    simulate_graph, simulate_momentum, verify_game,
)


@pytest.mark.parametrize("game", CANONICAL_GAMES)
def test_every_canonical_contract_parses_and_verifies(game) -> None:
    parsed = parse_game_spec_v1(game.model_dump(mode="json"))
    assert parsed.game_type == game.game_type
    assert verify_game(parsed)


@pytest.mark.parametrize(("solver", "game", "kwargs"), [
    (simulate_falling, CANONICAL_FALLING_GAME, {"height": 20}),
    (simulate_balance, CANONICAL_BALANCE_GAME, {"right_distance": 1}),
    (simulate_momentum, CANONICAL_MOMENTUM_GAME, {"player_velocity": -20}),
    (simulate_fraction, CANONICAL_FRACTION_GAME, {"selected_count": 1}),
    (simulate_graph, CANONICAL_GRAPH_GAME, {"slope": -2, "intercept": 3}),
])
def test_incorrect_attempt_loses(solver, game, kwargs) -> None:
    assert not solver(game, **kwargs).winnable


@pytest.mark.parametrize(("solver", "game", "kwargs"), [
    (simulate_falling, CANONICAL_FALLING_GAME, {"height": 19}),
    (simulate_balance, CANONICAL_BALANCE_GAME, {"right_distance": 10.1}),
    (simulate_momentum, CANONICAL_MOMENTUM_GAME, {"player_velocity": 31}),
    (simulate_fraction, CANONICAL_FRACTION_GAME, {"selected_count": 13}),
    (simulate_graph, CANONICAL_GRAPH_GAME, {"slope": 11, "intercept": 0}),
])
def test_attempt_bounds_are_enforced(solver, game, kwargs) -> None:
    with pytest.raises(ValueError, match="outside the supported control range"):
        solver(game, **kwargs)


@pytest.mark.parametrize(("game", "path", "value"), [
    (CANONICAL_FALLING_GAME, ("physics", "gravity"), 3.9),
    (CANONICAL_BALANCE_GAME, ("physics", "right_weight"), 101.0),
    (CANONICAL_MOMENTUM_GAME, ("solution_player_velocity",), 31.0),
    (CANONICAL_FRACTION_GAME, ("denominator",), 13),
    (CANONICAL_GRAPH_GAME, ("target_slope",), 10.1),
])
def test_contract_bounds_are_enforced(game, path, value) -> None:
    payload = game.model_dump(mode="json")
    target = payload
    for key in path[:-1]: target = target[key]
    target[path[-1]] = value
    with pytest.raises(ValidationError): parse_game_spec_v1(payload)


def test_fraction_requires_an_exact_partition() -> None:
    payload = CANONICAL_FRACTION_GAME.model_dump(mode="json")
    payload["total_items"] = 11
    with pytest.raises(ValidationError, match="divisible"): parse_game_spec_v1(payload)
