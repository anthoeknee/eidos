"""add_memory_indexes

Revision ID: add_memory_indexes
Revises: 4ebf055f29e5
Create Date: 2024-01-07 00:00:00.000000

"""

from typing import Sequence, Union
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "add_memory_indexes"
down_revision: Union[str, None] = "4ebf055f29e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # First, alter the column type to vector if it's not already
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    op.execute(
        "ALTER TABLE memories ALTER COLUMN embedding TYPE vector(1024) USING embedding::vector(1024);"
    )

    # Create index for channel_id lookups
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_memories_channel
        ON memories(channel_id);
    """)

    # Create index for vector similarity searches (now with dimensions specified)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_memories_embedding
        ON memories
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100);
    """)

    # Create index for timestamp-based queries
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_memories_timestamp
        ON memories(timestamp DESC);
    """)

    # Create index for memory type filtering
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_memories_type
        ON memories(memory_type);
    """)

    # Create GIN index for JSONB metadata queries
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_memories_metadata
        ON memories USING GIN (meta_data);
    """)


def downgrade() -> None:
    # Remove all indexes in reverse order
    op.execute("DROP INDEX IF EXISTS idx_memories_metadata;")
    op.execute("DROP INDEX IF EXISTS idx_memories_type;")
    op.execute("DROP INDEX IF EXISTS idx_memories_timestamp;")
    op.execute("DROP INDEX IF EXISTS idx_memories_embedding;")
    op.execute("DROP INDEX IF EXISTS idx_memories_channel;")

    # Optionally revert the column type back to text if needed
    op.execute("ALTER TABLE memories ALTER COLUMN embedding TYPE text;")
