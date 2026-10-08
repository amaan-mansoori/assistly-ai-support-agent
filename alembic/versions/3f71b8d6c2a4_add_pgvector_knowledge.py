"""add optional pgvector knowledge store

Revision ID: 3f71b8d6c2a4
Revises: 81e542527d02
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision = "3f71b8d6c2a4"
down_revision = "81e542527d02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"
    if is_postgres:
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "knowledge_records",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("source_id", sa.String(length=255), nullable=False),
        sa.Column("customer_tweet_id", sa.String(length=255), nullable=False),
        sa.Column("customer_message", sa.Text(), nullable=False),
        sa.Column("support_response", sa.Text(), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("embedding", Vector(384), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_knowledge_source_id", "knowledge_records", ["source_id"], unique=True)
    if is_postgres:
        op.execute(
            "CREATE INDEX ix_knowledge_embedding_hnsw "
            "ON knowledge_records USING hnsw (embedding vector_cosine_ops)"
        )
    else:
        op.create_index(
            "ix_knowledge_embedding_hnsw", "knowledge_records", ["embedding"]
        )


def downgrade() -> None:
    op.drop_index("ix_knowledge_embedding_hnsw", table_name="knowledge_records")
    op.drop_index("ix_knowledge_source_id", table_name="knowledge_records")
    op.drop_table("knowledge_records")
