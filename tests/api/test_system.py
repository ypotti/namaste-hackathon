from fastapi.testclient import TestClient

from math_puzzle_agent.api.app import create_app


class FakeDatabase:
    def __init__(self, available: bool = True) -> None:
        self.available = available
        self.started = False
        self.closed = False

    async def start(self) -> None:
        self.started = True

    async def close(self) -> None:
        self.closed = True

    async def ping(self) -> bool:
        return self.available


def test_health_and_database_lifecycle() -> None:
    database = FakeDatabase()
    with TestClient(create_app(database=database)) as client:
        assert database.started
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
    assert database.closed


def test_ready_when_database_is_available() -> None:
    with TestClient(create_app(database=FakeDatabase())) as client:
        response = client.get("/api/v1/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready", "database": "available"}


def test_ready_when_database_is_unavailable() -> None:
    with TestClient(create_app(database=FakeDatabase(available=False))) as client:
        response = client.get("/api/v1/ready")
    assert response.status_code == 503
    assert response.json() == {"status": "not_ready", "database": "unavailable"}
