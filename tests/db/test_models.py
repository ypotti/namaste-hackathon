from sqlalchemy import inspect

from math_puzzle_agent.db.models import Conversation, Game, GenerationRun, Message


def test_domain_tables_and_soft_delete_column_are_declared() -> None:
    assert Conversation.__tablename__ == "conversations"
    assert Message.__tablename__ == "messages"
    assert GenerationRun.__tablename__ == "generation_runs"
    assert Game.__tablename__ == "games"
    assert "deleted_at" in inspect(Conversation).columns


def test_child_foreign_keys_cascade_at_the_database_boundary() -> None:
    for model in (Message, GenerationRun, Game):
        conversation_id = inspect(model).columns.conversation_id
        foreign_key = next(iter(conversation_id.foreign_keys))
        assert foreign_key.ondelete == "CASCADE"


def test_required_json_contract_fields_are_non_nullable() -> None:
    game_columns = inspect(Game).columns
    assert not game_columns.spec.nullable
    assert not game_columns.solver_result.nullable
    assert not game_columns.schema_version.nullable
    assert not game_columns.contract_version.nullable

