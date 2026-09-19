"""pgvector memory embeddings"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
revision="0006_memory_vector"
down_revision="0005_autonomous_runtime"
branch_labels=None
depends_on=None
def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.add_column("memories",sa.Column("embedding",Vector(32),nullable=True))
def downgrade():
    op.drop_column("memories","embedding")
