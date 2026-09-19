"""event customer meeting action lifecycle finance v2"""
from alembic import op
import sqlalchemy as sa
from app import models
revision="0003_autonomous_loop"
down_revision="0002_action_memory_finance"
branch_labels=None
depends_on=None
def upgrade():
    bind=op.get_bind()
    for table in [models.Customer.__table__,models.Contact.__table__,models.CustomerInteraction.__table__,models.CustomerNote.__table__,models.Event.__table__,models.Meeting.__table__,models.MeetingParticipant.__table__,models.MeetingContribution.__table__,models.ActionAttempt.__table__,models.Budget.__table__]: table.create(bind,checkfirst=True)
    for name,typ in [("idempotency_key",sa.String(160)),("retry_count",sa.Integer()),("max_retries",sa.Integer()),("failure_reason",sa.Text()),("approved_by",sa.Uuid()),("approved_at",sa.DateTime(timezone=True)),("queued_at",sa.DateTime(timezone=True)),("started_at",sa.DateTime(timezone=True)),("finished_at",sa.DateTime(timezone=True))]: op.add_column("actions",sa.Column(name,typ,nullable=True))
    op.create_unique_constraint("uq_actions_idempotency_key","actions",["idempotency_key"])
    for name,typ in [("source",sa.String(80)),("customer_id",sa.Uuid()),("event_id",sa.Uuid()),("task_id",sa.Uuid()),("decision_id",sa.Uuid()),("meeting_id",sa.Uuid())]: op.add_column("memories",sa.Column(name,typ,nullable=True))
    for name,typ in [("status",sa.String(20)),("reference_type",sa.String(80)),("reference_id",sa.Uuid())]: op.add_column("transactions",sa.Column(name,typ,nullable=True))
def downgrade():
    for name in ["reference_id","reference_type","status"]: op.drop_column("transactions",name)
    for name in ["meeting_id","decision_id","task_id","event_id","customer_id","source"]: op.drop_column("memories",name)
    op.drop_constraint("uq_actions_idempotency_key","actions",type_="unique")
    for name in ["finished_at","started_at","queued_at","approved_at","approved_by","failure_reason","max_retries","retry_count","idempotency_key"]: op.drop_column("actions",name)
    bind=op.get_bind()
    for table in [models.Budget.__table__,models.ActionAttempt.__table__,models.MeetingContribution.__table__,models.MeetingParticipant.__table__,models.Meeting.__table__,models.Event.__table__,models.CustomerNote.__table__,models.CustomerInteraction.__table__,models.Contact.__table__,models.Customer.__table__]: table.drop(bind,checkfirst=True)
