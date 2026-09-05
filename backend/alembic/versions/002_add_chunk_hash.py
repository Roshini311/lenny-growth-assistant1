"""Add chunk_hash column to transcript_chunks for idempotency.

Revision ID: 002_add_chunk_hash
Revises: 001_initial_schema
Create Date: 2026-09-04 21:25:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002_add_chunk_hash'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('transcript_chunks', sa.Column('chunk_hash', sa.String(length=64), nullable=True))
    op.create_index('ix_transcript_chunks_chunk_hash', 'transcript_chunks', ['chunk_hash'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_transcript_chunks_chunk_hash', table_name='transcript_chunks')
    op.drop_column('transcript_chunks', 'chunk_hash')
    
