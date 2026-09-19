"""agent runtime v2"""
from alembic import op
from app import models
revision="0007_agent_runtime_v2"
down_revision="0006_memory_vector"
branch_labels=None
depends_on=None
def upgrade():
    bind=op.get_bind()
    for t in [models.AgentDecisionTrace.__table__,models.ActionResult.__table__,models.InformationRequest.__table__]:t.create(bind,checkfirst=True)
def downgrade():
    bind=op.get_bind()
    for t in [models.InformationRequest.__table__,models.ActionResult.__table__,models.AgentDecisionTrace.__table__]:t.drop(bind,checkfirst=True)
