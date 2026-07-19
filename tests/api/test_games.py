from fastapi.testclient import TestClient

from math_puzzle_agent.api.app import create_app
from math_puzzle_agent.games.schemas import parse_game_spec_v1
from math_puzzle_agent.games.registry import verify_game


class FakeDatabase:
    async def start(self) -> None:
        pass

    async def close(self) -> None:
        pass

    async def ping(self) -> bool:
        return True


def test_demo_game_uses_verified_public_contract() -> None:
    with TestClient(create_app(database=FakeDatabase())) as client:
        response = client.get("/api/v1/games/demo")

    assert response.status_code == 200
    spec = parse_game_spec_v1(response.json())
    assert spec.game_type == "projectile_target"
    assert verify_game(spec)
