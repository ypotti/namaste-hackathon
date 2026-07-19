"""Persist self-contained HTML artifacts for iframe delivery."""

from alembic import op
import sqlalchemy as sa

revision = "20260719_0002"
down_revision = "20260719_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("games", sa.Column("generated_html", sa.Text(), nullable=True))
    op.execute("UPDATE games SET generated_html = '<!doctype html><html><body><p>This game must be regenerated.</p></body></html>' WHERE generated_html IS NULL")
    op.alter_column("games", "generated_html", nullable=False)


def downgrade() -> None:
    op.drop_column("games", "generated_html")
