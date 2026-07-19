from math_puzzle_agent.db.checkpoints import checkpoint_database_url


def test_checkpoint_database_url_converts_sqlalchemy_drivers() -> None:
    assert checkpoint_database_url("postgresql+asyncpg://u:p@db/app") == "postgresql://u:p@db/app"
    assert checkpoint_database_url("postgresql+psycopg://u:p@db/app") == "postgresql://u:p@db/app"
    assert checkpoint_database_url("postgresql://u:p@db/app") == "postgresql://u:p@db/app"
