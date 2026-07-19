from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi.testclient import TestClient

from math_puzzle_agent.api.app import create_app
from math_puzzle_agent.api.routes import runs as run_routes
from math_puzzle_agent.db.models import GenerationRun
from math_puzzle_agent.db.repositories import get_session
from math_puzzle_agent.services.generation_runs import serialize_run


class FakeDatabase:
    async def start(self):
        pass

    async def close(self):
        pass


class FakeSession:
    pass


def make_run(status: str = "processing") -> GenerationRun:
    return GenerationRun(
        id=uuid.uuid4(), conversation_id=uuid.uuid4(), status=status, attempt_count=1,
        started_at=datetime(2026, 7, 19, tzinfo=UTC), completed_at=None,
    )


def client() -> TestClient:
    app = create_app(database=FakeDatabase())

    async def session_override():
        yield FakeSession()

    app.dependency_overrides[get_session] = session_override
    return TestClient(app)


def test_get_run_and_not_found(monkeypatch) -> None:
    run = make_run()

    class Service:
        def __init__(self, session):
            pass

        async def get(self, run_id):
            return run if run_id == run.id else None

        async def snapshot(self, run_id):
            return serialize_run(run) if run_id == run.id else None

    monkeypatch.setattr(run_routes, "GenerationRunService", Service)
    with client() as api:
        response = api.get(f"/api/v1/runs/{run.id}")
        assert response.status_code == 200
        assert response.json()["schema_version"] == "1.0"
        assert response.json()["status"] == "processing"
        assert api.get(f"/api/v1/runs/{uuid.uuid4()}").status_code == 404


def test_terminal_run_event_stream_and_resume(monkeypatch) -> None:
    run = make_run("completed")
    run.completed_at = datetime(2026, 7, 19, 0, 1, tzinfo=UTC)

    class Service:
        def __init__(self, session):
            pass

        async def get(self, run_id):
            return run

        async def events(self, run_id, *, after_version=0):
            yield f'id: {after_version + 1}\nevent: run.updated\ndata: {{"event_version": {after_version + 1}}}\n\n'

    monkeypatch.setattr(run_routes, "GenerationRunService", Service)
    with client() as api:
        response = api.get(f"/api/v1/runs/{run.id}/events", headers={"Last-Event-ID": "4"})
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        assert "id: 5" in response.text
        invalid = api.get(f"/api/v1/runs/{run.id}/events", headers={"Last-Event-ID": "bad"})
        assert invalid.status_code == 400
