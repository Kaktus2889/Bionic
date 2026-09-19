"""goal kpi foundation"""
from alembic import op
from app import models
revision="0004_goal_kpi"
down_revision="0003_autonomous_loop"
branch_labels=None
depends_on=None
def upgrade():
 bind=op.get_bind(); models.Goal.__table__.create(bind,checkfirst=True); models.KPI.__table__.create(bind,checkfirst=True)
def downgrade():
 bind=op.get_bind(); models.KPI.__table__.drop(bind,checkfirst=True); models.Goal.__table__.drop(bind,checkfirst=True)
