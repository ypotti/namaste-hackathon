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


def test_list_games(monkeypatch) -> None:
    class FakeGameRecord:
        id = "12345678-1234-5678-1234-567812345678"
        conversation_id = "12345678-1234-5678-1234-567812345678"
        generation_run_id = "12345678-1234-5678-1234-567812345678"
        schema_version = "1.0"
        contract_version = "1.0"
        game_type = "projectile_target"
        title = "Mock Game Title"
        concept = "Mock Concept"
        verification_status = "verified"
        solver_result = {}
        spec = {
            "title": "Mock Game Title",
            "math_concept": "Mock Concept",
            "scene_description": "Desc",
            "question": "Q?",
            "known_values": [{"name": "A", "value": "1"}],
            "learner_answer_label": "Ans",
            "correct_answer": 1.0,
            "accepted_tolerance": 0.1,
            "formulas": ["x = 1"],
            "solution_steps": ["Step 1", "Step 2"],
            "hint": "Hint",
            "animation_description": "Anim",
        }
        created_at = "2026-07-19T21:00:00Z"
        updated_at = "2026-07-19T21:00:00Z"

    class FakeGames:
        def __init__(self, ignored_session) -> None:
            pass

        async def list_all(self):
            return [FakeGameRecord()]

    from math_puzzle_agent.api.routes import games as game_routes
    from math_puzzle_agent.db.repositories import get_session
    monkeypatch.setattr(game_routes, "GameRepository", FakeGames)

    app = create_app(database=FakeDatabase())
    async def override_session():
        yield None
    app.dependency_overrides[get_session] = override_session

    with TestClient(app) as client:
        response = client.get("/api/v1/games")

    assert response.status_code == 200
    games = response.json()
    assert len(games) == 1
    assert games[0]["title"] == "Mock Game Title"
