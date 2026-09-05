"""Initial database schema with pgvector extension and HNSW index.

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-09-04 21:20:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Enable pgvector extension if vector extension is installed in PostgreSQL instance
    conn = op.get_bind()
    has_vector_ext = (conn.scalar(sa.text("SELECT count(*) FROM pg_available_extensions WHERE name = 'vector'")) or 0) > 0

    if has_vector_ext:
        op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # 2. Create sessions table
    op.create_table(
        'sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 3. Create messages table
    op.create_table(
        'messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=True),
        sa.Column('sources', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_messages_session_id', 'messages', ['session_id'])

    # 4. Create artifacts table
    op.create_table(
        'artifacts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('messages.id', ondelete='SET NULL'), nullable=True),
        sa.Column('artifact_type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_artifacts_session_id', 'artifacts', ['session_id'])
    op.create_index('ix_artifacts_message_id', 'artifacts', ['message_id'])

    # 5. Create transcript_chunks table
    embedding_col = Vector(384) if has_vector_ext else sa.ARRAY(sa.Float)
    op.create_table(
        'transcript_chunks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('guest', sa.String(length=255), nullable=False),
        sa.Column('episode_title', sa.String(length=255), nullable=False),
        sa.Column('publish_date', sa.String(length=50), nullable=True),
        sa.Column('timestamp', sa.String(length=50), nullable=True),
        sa.Column('speaker', sa.String(length=255), nullable=True),
        sa.Column('chunk_text', sa.Text(), nullable=False),
        sa.Column('source_url', sa.String(length=500), nullable=True),
        sa.Column('embedding', embedding_col, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_transcript_chunks_guest', 'transcript_chunks', ['guest'])
    op.create_index('ix_transcript_chunks_episode_title', 'transcript_chunks', ['episode_title'])

    # 6. Create HNSW index for vector cosine similarity (<->)
    if has_vector_ext:
        op.execute(
            "CREATE INDEX IF NOT EXISTS idx_chunks_embedding "
            "ON transcript_chunks USING hnsw (embedding vector_cosine_ops) "
            "WITH (m = 16, ef_construction = 64);"
        )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_chunks_embedding;")
    op.drop_table('transcript_chunks')
    op.drop_table('artifacts')
    op.drop_table('messages')
    op.drop_table('sessions')
    op.execute("DROP EXTENSION IF EXISTS vector CASCADE;")
