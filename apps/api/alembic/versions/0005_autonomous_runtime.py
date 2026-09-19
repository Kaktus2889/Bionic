"""autonomous runtime planning and KPI history"""
from alembic import op
import sqlalchemy as sa
from app import models
revision="0005_autonomous_runtime"
down_revision="0004_goal_kpi"
branch_labels=None
depends_on=None
def upgrade():
    bind=op.get_bind()
    if bind.dialect.name=="postgresql":
        op.execute("ALTER TYPE companystatus ADD VALUE IF NOT EXISTS 'RUNNING'")
        op.execute("ALTER TYPE companystatus ADD VALUE IF NOT EXISTS 'ERROR'")
    for table in [models.KPIObservation.__table__,models.StrategyRevision.__table__,models.Plan.__table__,models.CompanyCycle.__table__]:
        table.create(bind,checkfirst=True)
def downgrade():
    bind=op.get_bind()
    for table in [models.CompanyCycle.__table__,models.Plan.__table__,models.StrategyRevision.__table__,models.KPIObservation.__table__]:
        table.drop(bind,checkfirst=True)
