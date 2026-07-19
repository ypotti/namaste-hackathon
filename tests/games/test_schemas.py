from __future__ import annotations

import copy

import pytest
from pydantic import ValidationError

from math_puzzle_agent.games import CANONICAL_PROJECTILE_GAME, parse_game_spec_v1
from math_puzzle_agent.games.schemas import ProjectileTargetSpecV1


def fixture_payload() -> dict:
    return CANONICAL_PROJECTILE_GAME.model_dump(mode="json")


def test_canonical_fixture_round_trips_through_discriminated_contract() -> None:
    parsed = parse_game_spec_v1(fixture_payload())

    assert isinstance(parsed, ProjectileTargetSpecV1)
    assert parsed.schema_version == "1.0"
    assert parsed.game_type == "projectile_target"
    assert parsed.renderer_version == "projectile-svg@1"
    assert parsed.solver_version == "projectile@1"


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("schema_version",), "2.0"),
        (("game_type",), "arbitrary_html"),
        (("difficulty",), "impossible"),
        (("scene", "theme"), "model_invented_scene"),
        (("physics", "gravity"), 3.99),
        (("physics", "gravity"), 16.01),
        (("physics", "target_x"), 479),
        (("physics", "target_x"), 736),
        (("physics", "target_y"), 89),
        (("physics", "target_y"), 331),
        (("solution", "angle"), 19),
        (("solution", "angle"), 66),
        (("solution", "power"), 54),
        (("solution", "power"), 101),
    ],
)
def test_rejects_values_outside_renderer_contract(path: tuple[str, ...], value: object) -> None:
    payload = fixture_payload()
    target = payload
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value

    with pytest.raises(ValidationError):
        parse_game_spec_v1(payload)


def test_rejects_unknown_fields_at_every_contract_boundary() -> None:
    for path in [(), ("scene",), ("physics",), ("learning",), ("controls", "angle")]:
        payload = fixture_payload()
        target = payload
        for key in path:
            target = target[key]
        target["custom_css"] = "body { display: none }"

        with pytest.raises(ValidationError):
            parse_game_spec_v1(payload)


@pytest.mark.parametrize("field", ["title", "concept", "eyebrow", "instructions"])
def test_rejects_blank_required_copy(field: str) -> None:
    payload = fixture_payload()
    payload[field] = "   "

    with pytest.raises(ValidationError):
        parse_game_spec_v1(payload)


def test_rejects_coerced_numeric_strings() -> None:
    payload = fixture_payload()
    payload["physics"]["gravity"] = "9.8"

    with pytest.raises(ValidationError):
        parse_game_spec_v1(payload)


def test_contract_dump_is_independent_data() -> None:
    payload = copy.deepcopy(fixture_payload())
    payload["title"] = "Different"

    assert CANONICAL_PROJECTILE_GAME.title == "Arc Runner"
