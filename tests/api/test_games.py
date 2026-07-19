from fastapi.testclient import TestClient

from math_puzzle_agent.api.app import create_app
from math_puzzle_agent.schemas import PuzzleSpec


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
    spec = PuzzleSpec.model_validate(response.json())
    assert spec.title == "The 3–4–5 Triangle Challenge"
    assert spec.math_concept == "Pythagorean theorem"


def test_demo_game_html_is_iframe_ready() -> None:
    with TestClient(create_app(database=FakeDatabase())) as client:
        response = client.get("/api/v1/games/demo/content")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert response.headers["x-frame-options"] == "SAMEORIGIN"
    csp = response.headers["content-security-policy"]
    assert "https://cdn.jsdelivr.net" in csp
    assert "sandbox" not in response.text.lower()
    assert "<!doctype html>" in response.text.lower()
    assert "The 3–4–5 Triangle Challenge" in response.text
