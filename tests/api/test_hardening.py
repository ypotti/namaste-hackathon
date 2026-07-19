from fastapi import HTTPException
from fastapi.testclient import TestClient

from math_puzzle_agent.api.app import create_app
from math_puzzle_agent.api.settings import APISettings
from math_puzzle_agent.api.security import InMemoryFixedWindowRateLimiter


class FakeDatabase:
    async def start(self):
        pass

    async def close(self):
        pass

    async def ping(self):
        return True


def hardened_app(**overrides):
    settings = APISettings(
        cors_allowed_origins="https://ui.example",
        generation_rate_limit_requests=1,
        generation_rate_limit_window_seconds=60,
        **overrides,
    )
    app = create_app(settings=settings, database=FakeDatabase())

    @app.get("/api/v1/test-http-error")
    async def http_error():
        raise HTTPException(status_code=403, detail="Not allowed")

    @app.get("/api/v1/test-crash")
    async def crash():
        raise RuntimeError("secret database detail")

    return app


def test_request_id_and_security_headers_are_added() -> None:
    with TestClient(hardened_app()) as client:
        response = client.get("/api/v1/health", headers={"X-Request-ID": "trace-123"})
    assert response.headers["x-request-id"] == "trace-123"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["content-security-policy"].startswith("default-src 'none'")


def test_cors_is_restricted_to_configured_origin() -> None:
    with TestClient(hardened_app()) as client:
        allowed = client.options(
            "/api/v1/health",
            headers={"Origin": "https://ui.example", "Access-Control-Request-Method": "GET"},
        )
        denied = client.options(
            "/api/v1/health",
            headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "GET"},
        )
    assert allowed.headers["access-control-allow-origin"] == "https://ui.example"
    assert "access-control-allow-origin" not in denied.headers


def test_public_errors_are_enveloped_and_internal_details_are_hidden() -> None:
    with TestClient(hardened_app(), raise_server_exceptions=False) as client:
        forbidden = client.get("/api/v1/test-http-error")
        crashed = client.get("/api/v1/test-crash")
    assert forbidden.json()["error"]["message"] == "Not allowed"
    assert forbidden.json()["error"]["request_id"] == forbidden.headers["x-request-id"]
    assert crashed.status_code == 500
    assert crashed.json()["error"]["code"] == "internal_error"
    assert "secret" not in crashed.text


def test_oversize_request_and_generation_rate_limit() -> None:
    with TestClient(hardened_app(max_request_body_bytes=64), raise_server_exceptions=False) as client:
        oversized = client.post("/api/v1/conversations", content=b"x" * 65)
        first = client.post("/api/v1/conversations/abc/messages", json={"content": "one"})
        limited = client.post("/api/v1/conversations/abc/messages", json={"content": "two"})
    assert oversized.status_code == 413
    assert first.status_code != 429
    assert limited.status_code == 429
    assert int(limited.headers["retry-after"]) > 0


def test_fixed_window_rate_limiter_resets() -> None:
    limiter = InMemoryFixedWindowRateLimiter(requests=1, window_seconds=10)
    assert limiter.check("client", now=0) == (True, 0)
    assert limiter.check("client", now=1)[0] is False
    assert limiter.check("client", now=10) == (True, 0)
