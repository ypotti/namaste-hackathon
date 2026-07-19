"""Create PhysicsForge application tables."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260719_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("conversations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.Text()), sa.Column("status", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True)))
    op.create_table("messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.Text(), nullable=False), sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_messages_conversation_created", "messages", ["conversation_id", "created_at"])
    op.create_table("generation_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.Text(), nullable=False), sa.Column("puzzle_spec", postgresql.JSONB()),
        sa.Column("candidate_game_spec", postgresql.JSONB()), sa.Column("solver_result", postgresql.JSONB()),
        sa.Column("review_result", postgresql.JSONB()), sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("error_code", sa.Text()), sa.Column("error_message", sa.Text()),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)))
    op.create_index("ix_generation_runs_conversation_started", "generation_runs", ["conversation_id", "started_at"])
    op.create_index("ix_generation_runs_status", "generation_runs", ["status"])
    op.create_table("games",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("generation_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("generation_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("schema_version", sa.Text(), nullable=False), sa.Column("contract_version", sa.Text(), nullable=False),
        sa.Column("game_type", sa.Text(), nullable=False), sa.Column("title", sa.Text(), nullable=False), sa.Column("concept", sa.Text(), nullable=False),
        sa.Column("spec", postgresql.JSONB(), nullable=False), sa.Column("verification_status", sa.Text(), nullable=False),
        sa.Column("solver_result", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_games_conversation_created", "games", ["conversation_id", "created_at"])
    op.create_index("ix_games_game_type", "games", ["game_type"])


def downgrade() -> None:
    op.drop_table("games")
    op.drop_table("generation_runs")
    op.drop_table("messages")
    op.drop_table("conversations")
