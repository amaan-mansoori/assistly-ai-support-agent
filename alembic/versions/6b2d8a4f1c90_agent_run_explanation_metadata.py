"""persist structured agent explanation and stage metadata

Revision ID: 6b2d8a4f1c90
Revises: 3f71b8d6c2a4
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "6b2d8a4f1c90"
down_revision = "3f71b8d6c2a4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "agent_runs",
        sa.Column("intent_confidence", sa.Float(), nullable=True),
    )
    op.add_column(
        "agent_runs",
        sa.Column("intent_reason", sa.Text(), nullable=True),
    )
    op.add_column(
        "agent_runs",
        sa.Column("intent_source", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "agent_runs",
        sa.Column("evidence_reason", sa.Text(), nullable=True),
    )
    op.add_column(
        "agent_runs",
        sa.Column(
            "processing_metadata",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
    )


def downgrade() -> None:
    op.drop_column("agent_runs", "processing_metadata")
    op.drop_column("agent_runs", "evidence_reason")
    op.drop_column("agent_runs", "intent_source")
    op.drop_column("agent_runs", "intent_reason")
    op.drop_column("agent_runs", "intent_confidence")
