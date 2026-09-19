"""action memory finance"""
from alembic import op
from app.db import Base
from app import models
revision="0002_action_memory_finance"
down_revision="0001_core"
branch_labels=None
depends_on=None
def upgrade():
    bind=op.get_bind()
    for table in [models.Action.__table__,models.Memory.__table__,models.CompanyAccount.__table__,models.Transaction.__table__]: table.create(bind,checkfirst=True)
def downgrade():
    bind=op.get_bind()
    for table in [models.Transaction.__table__,models.CompanyAccount.__table__,models.Memory.__table__,models.Action.__table__]: table.drop(bind,checkfirst=True)
