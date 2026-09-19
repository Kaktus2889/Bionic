import enum,uuid
from datetime import datetime,timezone
from sqlalchemy import String,Text,DateTime,ForeignKey,Enum,Float,Integer,JSON,Index
from sqlalchemy.orm import Mapped,mapped_column
from .db import Base
def now(): return datetime.now(timezone.utc)
class CompanyStatus(str,enum.Enum): PAUSED="PAUSED"; REALTIME="REALTIME"; FAST="FAST"; SIMULATION="SIMULATION"
class Autonomy(str,enum.Enum): MANUAL="MANUAL"; SEMI_AUTONOMOUS="SEMI_AUTONOMOUS"; AUTONOMOUS="AUTONOMOUS"
class TaskStatus(str,enum.Enum): BACKLOG="BACKLOG"; TODO="TODO"; IN_PROGRESS="IN_PROGRESS"; REVIEW="REVIEW"; BLOCKED="BLOCKED"; DONE="DONE"; CANCELLED="CANCELLED"
class Priority(str,enum.Enum): LOW="LOW"; MEDIUM="MEDIUM"; HIGH="HIGH"; CRITICAL="CRITICAL"
class Stamp:
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now,nullable=False)
    updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now,onupdate=now,nullable=False)
class Company(Stamp,Base):
    __tablename__="companies"
    id:Mapped[uuid.UUID]=mapped_column(primary_key=True,default=uuid.uuid4)
    name:Mapped[str]=mapped_column(String(160)); industry:Mapped[str]=mapped_column(String(160)); capital:Mapped[float]=mapped_column(Float); cash:Mapped[float]=mapped_column(Float); goal:Mapped[str]=mapped_column(Text); horizon_days:Mapped[int]=mapped_column(Integer); autonomy:Mapped[Autonomy]=mapped_column(Enum(Autonomy)); risk_tolerance:Mapped[str]=mapped_column(String(32)); status:Mapped[CompanyStatus]=mapped_column(Enum(CompanyStatus),default=CompanyStatus.PAUSED); speed:Mapped[int]=mapped_column(Integer,default=1); tick_number:Mapped[int]=mapped_column(Integer,default=0)
class Agent(Stamp,Base):
    __tablename__="agents"
    id:Mapped[uuid.UUID]=mapped_column(primary_key=True,default=uuid.uuid4); company_id:Mapped[uuid.UUID]=mapped_column(ForeignKey("companies.id",ondelete="CASCADE"),index=True); name:Mapped[str]=mapped_column(String(120)); position:Mapped[str]=mapped_column(String(120)); department:Mapped[str]=mapped_column(String(120)); role_description:Mapped[str]=mapped_column(Text,default=""); personality:Mapped[dict]=mapped_column(JSON,default=dict); skills:Mapped[list]=mapped_column(JSON,default=list); goals:Mapped[list]=mapped_column(JSON,default=list); kpis:Mapped[dict]=mapped_column(JSON,default=dict); status:Mapped[str]=mapped_column(String(32),default="ACTIVE"); manager_id:Mapped[uuid.UUID|None]=mapped_column(ForeignKey("agents.id",ondelete="SET NULL"),nullable=True); permission_level:Mapped[int]=mapped_column(Integer,default=1); knowledge_scope:Mapped[list]=mapped_column(JSON,default=list)
class Task(Stamp,Base):
    __tablename__="tasks"
    id:Mapped[uuid.UUID]=mapped_column(primary_key=True,default=uuid.uuid4); company_id:Mapped[uuid.UUID]=mapped_column(ForeignKey("companies.id",ondelete="CASCADE"),index=True); title:Mapped[str]=mapped_column(String(240)); description:Mapped[str]=mapped_column(Text,default=""); creator_id:Mapped[uuid.UUID|None]=mapped_column(ForeignKey("agents.id",ondelete="SET NULL"),nullable=True); assignee_id:Mapped[uuid.UUID|None]=mapped_column(ForeignKey("agents.id",ondelete="SET NULL"),nullable=True); parent_task_id:Mapped[uuid.UUID|None]=mapped_column(ForeignKey("tasks.id",ondelete="SET NULL"),nullable=True); priority:Mapped[Priority]=mapped_column(Enum(Priority),default=Priority.MEDIUM); status:Mapped[TaskStatus]=mapped_column(Enum(TaskStatus),default=TaskStatus.TODO); deadline:Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True); estimated_effort:Mapped[float|None]=mapped_column(Float,nullable=True); actual_effort:Mapped[float|None]=mapped_column(Float,nullable=True); dependencies:Mapped[list]=mapped_column(JSON,default=list); blocked_reason:Mapped[str|None]=mapped_column(Text,nullable=True); completed_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True)
class Channel(Stamp,Base):
    __tablename__="channels"
    id:Mapped[uuid.UUID]=mapped_column(primary_key=True,default=uuid.uuid4); company_id:Mapped[uuid.UUID]=mapped_column(ForeignKey("companies.id",ondelete="CASCADE"),index=True); name:Mapped[str]=mapped_column(String(80)); allowed_departments:Mapped[list]=mapped_column(JSON,default=list)
class Message(Base):
    __tablename__="messages"
    id:Mapped[uuid.UUID]=mapped_column(primary_key=True,default=uuid.uuid4); company_id:Mapped[uuid.UUID]=mapped_column(ForeignKey("companies.id",ondelete="CASCADE"),index=True); channel_id:Mapped[uuid.UUID]=mapped_column(ForeignKey("channels.id",ondelete="CASCADE"),index=True); sender_id:Mapped[uuid.UUID|None]=mapped_column(ForeignKey("agents.id",ondelete="SET NULL"),nullable=True); content:Mapped[str]=mapped_column(Text); thread_id:Mapped[uuid.UUID|None]=mapped_column(nullable=True); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now,index=True)
class Decision(Base):
    __tablename__="decisions"
    id:Mapped[uuid.UUID]=mapped_column(primary_key=True,default=uuid.uuid4); company_id:Mapped[uuid.UUID]=mapped_column(ForeignKey("companies.id",ondelete="CASCADE"),index=True); title:Mapped[str]=mapped_column(String(240)); problem:Mapped[str]=mapped_column(Text); context:Mapped[dict]=mapped_column(JSON,default=dict); options:Mapped[list]=mapped_column(JSON,default=list); participants:Mapped[list]=mapped_column(JSON,default=list); arguments:Mapped[dict]=mapped_column(JSON,default=dict); risk:Mapped[str]=mapped_column(String(32)); cost:Mapped[float]=mapped_column(Float,default=0); expected_outcome:Mapped[str]=mapped_column(Text); final_decision:Mapped[str]=mapped_column(Text); decided_by:Mapped[uuid.UUID|None]=mapped_column(ForeignKey("agents.id",ondelete="SET NULL"),nullable=True); result:Mapped[str|None]=mapped_column(Text,nullable=True); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
class Activity(Base):
    __tablename__="activities"
    id:Mapped[uuid.UUID]=mapped_column(primary_key=True,default=uuid.uuid4); company_id:Mapped[uuid.UUID]=mapped_column(ForeignKey("companies.id",ondelete="CASCADE"),index=True); agent_id:Mapped[uuid.UUID|None]=mapped_column(ForeignKey("agents.id",ondelete="SET NULL"),nullable=True); action:Mapped[str]=mapped_column(String(120)); module:Mapped[str]=mapped_column(String(120)); status:Mapped[str]=mapped_column(String(32),default="OK"); detail:Mapped[str]=mapped_column(Text); duration_ms:Mapped[int]=mapped_column(Integer,default=0); error:Mapped[str|None]=mapped_column(Text,nullable=True); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now,index=True)
class LLMUsage(Base):
    __tablename__="llm_usage"
    id:Mapped[uuid.UUID]=mapped_column(primary_key=True,default=uuid.uuid4); provider:Mapped[str]=mapped_column(String(80)); model:Mapped[str]=mapped_column(String(120)); agent_id:Mapped[uuid.UUID|None]=mapped_column(ForeignKey("agents.id",ondelete="SET NULL"),nullable=True); company_id:Mapped[uuid.UUID]=mapped_column(ForeignKey("companies.id",ondelete="CASCADE"),index=True); task_id:Mapped[uuid.UUID|None]=mapped_column(ForeignKey("tasks.id",ondelete="SET NULL"),nullable=True); prompt_tokens:Mapped[int]=mapped_column(Integer); completion_tokens:Mapped[int]=mapped_column(Integer); cost:Mapped[float]=mapped_column(Float); latency:Mapped[int]=mapped_column(Integer); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
Index("ix_tasks_company_status",Task.company_id,Task.status)
