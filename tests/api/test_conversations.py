from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi.testclient import TestClient

from math_puzzle_agent.api.app import create_app
from math_puzzle_agent.api.routes import conversations as conversation_routes
from math_puzzle_agent.api.routes import games as game_routes
from math_puzzle_agent.db.models import Conversation, Game, GenerationRun, Message
from math_puzzle_agent.db.repositories import get_session
from math_puzzle_agent.games.fixtures import CANONICAL_PROJECTILE_GAME
from math_puzzle_agent.games.html_renderer import render_game_html


NOW = datetime(2026, 7, 19, 8, 0, tzinfo=UTC)


class FakeDatabase:
    async def start(self) -> None:
        pass

    async def close(self) -> None:
        pass

    async def ping(self) -> bool:
        return True


class FakeTransaction:
    def __init__(self) -> None:
        self.committed = False
        self.rolled_back = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback) -> None:
        self.committed = exc_type is None
        self.rolled_back = exc_type is not None


class FakeSession:
    def __init__(self) -> None:
        self.transactions: list[FakeTransaction] = []

    def begin(self) -> FakeTransaction:
        transaction = FakeTransaction()
        self.transactions.append(transaction)
        return transaction


def conversation(*, title: str | None = None, deleted: bool = False) -> Conversation:
    item = Conversation(
        id=uuid.uuid4(),
        title=title,
        status="deleted" if deleted else "active",
        created_at=NOW,
        updated_at=NOW,
        deleted_at=NOW if deleted else None,
    )
    return item


def game_record(conversation_id: uuid.UUID) -> Game:
    spec = CANONICAL_PROJECTILE_GAME
    run_id = uuid.uuid4()
    return Game(
        id=uuid.uuid4(),
        conversation_id=conversation_id,
        generation_run_id=run_id,
        schema_version=spec.schema_version,
        contract_version=spec.renderer_version,
        game_type=spec.game_type,
        title=spec.title,
        concept=spec.concept,
        spec=spec.model_dump(mode="json"),
        generated_html=render_game_html(spec),
        verification_status="verified",
        solver_result={"winnable": True},
        created_at=NOW,
        updated_at=NOW,
    )


def message_record(conversation_id: uuid.UUID, *, role: str, content: str) -> Message:
    return Message(
        id=uuid.uuid4(),
        conversation_id=conversation_id,
        role=role,
        content=content,
        message_metadata={},
        created_at=NOW,
    )


def client_for(session: FakeSession, *, raise_server_exceptions: bool = True) -> TestClient:
    app = create_app(database=FakeDatabase())

    async def override_session():
        yield session

    app.dependency_overrides[get_session] = override_session
    return TestClient(app, raise_server_exceptions=raise_server_exceptions)


def test_create_list_get_and_soft_delete_conversation(monkeypatch) -> None:
    session = FakeSession()
    items: dict[uuid.UUID, Conversation] = {}

    class FakeConversations:
        def __init__(self, ignored_session) -> None:
            pass

        async def create(self, *, title=None):
            item = conversation(title=title)
            items[item.id] = item
            return item

        async def list_active(self):
            return [item for item in items.values() if item.deleted_at is None]

        async def get_active(self, conversation_id):
            item = items.get(conversation_id)
            return item if item is not None and item.deleted_at is None else None

        async def soft_delete(self, item):
            item.status = "deleted"
            item.deleted_at = NOW

    monkeypatch.setattr(conversation_routes, "ConversationRepository", FakeConversations)

    with client_for(session) as client:
        created = client.post("/api/v1/conversations", json={"title": "  Motion lab  "})
        assert created.status_code == 201
        assert created.json()["title"] == "Motion lab"
        conversation_id = created.json()["id"]

        assert [item["id"] for item in client.get("/api/v1/conversations").json()] == [conversation_id]
        assert client.get(f"/api/v1/conversations/{conversation_id}").json()["status"] == "active"
        assert client.delete(f"/api/v1/conversations/{conversation_id}").status_code == 204

        assert client.get("/api/v1/conversations").json() == []
        assert client.get(f"/api/v1/conversations/{conversation_id}").status_code == 404
        assert client.delete(f"/api/v1/conversations/{conversation_id}").status_code == 404

    assert session.transactions[0].committed  # create
    assert session.transactions[1].committed  # first delete
    assert session.transactions[2].rolled_back  # repeated delete raises 404


def test_missing_conversation_children_are_not_exposed(monkeypatch) -> None:
    class MissingConversations:
        def __init__(self, ignored_session) -> None:
            pass

        async def get_active(self, conversation_id):
            return None

    monkeypatch.setattr(conversation_routes, "ConversationRepository", MissingConversations)

    missing_id = uuid.uuid4()
    with client_for(FakeSession()) as client:
        assert client.get(f"/api/v1/conversations/{missing_id}/messages").status_code == 404
        assert client.get(f"/api/v1/conversations/{missing_id}/games").status_code == 404
        assert client.post(
            f"/api/v1/conversations/{missing_id}/messages", json={"content": "Make a game"}
        ).status_code == 404


def test_message_submission_returns_and_persists_ready_game(monkeypatch) -> None:
    session = FakeSession()
    active = conversation(title="Projectile motion")
    stored_messages: list[Message] = []
    stored_game = game_record(active.id)

    class FakeConversations:
        def __init__(self, ignored_session) -> None:
            pass

        async def get_active(self, conversation_id):
            return active if conversation_id == active.id else None

    class FakeMessages:
        def __init__(self, ignored_session) -> None:
            pass

        async def list_for_conversation(self, conversation_id):
            return stored_messages

    class FakeGames:
        def __init__(self, ignored_session) -> None:
            pass

        async def list_for_conversation(self, conversation_id):
            return [stored_game]

        async def get(self, game_id):
            return stored_game if game_id == stored_game.id else None

    class FakeGeneration:
        def __init__(self, ignored_session) -> None:
            pass

        async def submit_message(self, *, conversation_id, content):
            user = message_record(conversation_id, role="user", content=content)
            assistant = message_record(conversation_id, role="assistant", content="Your game is ready.")
            assistant.message_metadata = {
                "status": "ready",
                "run_id": str(stored_game.generation_run_id),
                "game_id": str(stored_game.id),
            }
            stored_messages.extend([user, assistant])
            return user, stored_game, assistant

    monkeypatch.setattr(conversation_routes, "ConversationRepository", FakeConversations)
    monkeypatch.setattr(conversation_routes, "MessageRepository", FakeMessages)
    monkeypatch.setattr(conversation_routes, "GameRepository", FakeGames)
    monkeypatch.setattr(conversation_routes, "ConversationGenerationService", FakeGeneration)
    monkeypatch.setattr(game_routes, "GameRepository", FakeGames)

    with client_for(session) as client:
        response = client.post(
            f"/api/v1/conversations/{active.id}/messages",
            json={"content": "  Build a ball and hoop puzzle  "},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "ready"
        assert payload["game_id"] == str(stored_game.id)
        assert payload["run_id"] == str(stored_game.generation_run_id)
        assert payload["game"]["game_type"] == "projectile_target"
        assert payload["assistant_message"]["metadata"]["status"] == "ready"

        messages = client.get(f"/api/v1/conversations/{active.id}/messages").json()
        assert [item["role"] for item in messages] == ["user", "assistant"]
        assert messages[0]["content"] == "Build a ball and hoop puzzle"

        games = client.get(f"/api/v1/conversations/{active.id}/games").json()
        assert [item["id"] for item in games] == [str(stored_game.id)]
        assert games[0]["verification_status"] == "verified"
        fetched_game = client.get(f"/api/v1/games/{stored_game.id}")
        assert fetched_game.status_code == 200
        assert fetched_game.json()["spec"]["title"] == stored_game.spec["title"]
        game_content = client.get(f"/api/v1/games/{stored_game.id}/content")
        assert game_content.status_code == 200
        assert game_content.text == stored_game.generated_html
        assert game_content.headers["x-frame-options"] == "SAMEORIGIN"
        assert client.get(f"/api/v1/games/{uuid.uuid4()}").status_code == 404

    assert session.transactions[-1].committed


def test_message_generation_error_rolls_back_transaction(monkeypatch) -> None:
    session = FakeSession()
    active = conversation()

    class FakeConversations:
        def __init__(self, ignored_session) -> None:
            pass

        async def get_active(self, conversation_id):
            return active

    class FailingGeneration:
        def __init__(self, ignored_session) -> None:
            pass

        async def submit_message(self, **kwargs):
            raise RuntimeError("generation failed")

    monkeypatch.setattr(conversation_routes, "ConversationRepository", FakeConversations)
    monkeypatch.setattr(conversation_routes, "ConversationGenerationService", FailingGeneration)

    with client_for(session, raise_server_exceptions=False) as client:
        response = client.post(
            f"/api/v1/conversations/{active.id}/messages", json={"content": "Build a puzzle"}
        )

    assert response.status_code == 500
    assert session.transactions[-1].rolled_back
