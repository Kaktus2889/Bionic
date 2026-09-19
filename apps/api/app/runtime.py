from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import Company,CompanyStatus,CompanyCycle,Goal,StrategyRevision,Plan,Activity,Channel,Message,now
from .kpi import KPIEngine
from .strategy import StrategyEngine
from .planning import PlanningEngine
from .agent_runtime import AgentRuntime
from .config import settings
class CompanyRuntime:
    async def cycle(self,db:Session,company:Company)->CompanyCycle:
        tick=company.tick_number+1;key=f"{company.id}:{tick}";old=db.scalar(select(CompanyCycle).where(CompanyCycle.idempotency_key==key))
        if old and old.status=="COMPLETED":return old
        cycle=old or CompanyCycle(company_id=company.id,tick=tick,idempotency_key=key,status="RUNNING",phase="OBSERVE");db.add(cycle);db.flush()
        try:
            kpis=KPIEngine().measure(db,company)
            if tick==1:
                channel=db.scalar(select(Channel).where(Channel.company_id==company.id,Channel.name=="general"));goal0=db.scalar(select(Goal).where(Goal.company_id==company.id,Goal.status=="ACTIVE"));db.add(Message(company_id=company.id,channel_id=channel.id,sender_id=goal0.owner_id,content=f"Autonomous runtime started. Goal: {goal0.title}"))
            cycle.phase="STRATEGY";strategy=StrategyEngine().review(db,company,kpis,force=tick==1 or tick%settings.company_review_interval==0)
            goal=db.scalar(select(Goal).where(Goal.company_id==company.id,Goal.status=="ACTIVE"));cycle.phase="PLAN"
            active=db.scalar(select(Plan).where(Plan.company_id==company.id,Plan.status=="ACTIVE").order_by(Plan.created_at.desc()))
            if not active or tick==1 or (tick%settings.company_review_interval==0 and active.strategy_id!=strategy.id):
                active=await PlanningEngine().create(db,company,goal,strategy,kpis,f"{company.id}:{strategy.id}")
            cycle.phase="AGENT_ACTIONS";AgentRuntime().step(db,company);cycle.phase="MEASURE";KPIEngine().measure(db,company)
            company.tick_number=tick;cycle.status="COMPLETED";cycle.phase="DONE";cycle.finished_at=now();db.add(Activity(company_id=company.id,agent_id=goal.owner_id,action="COMPANY_CYCLE_COMPLETED",module="runtime",detail=f"tick={tick}; plan={active.id}"));return cycle
        except Exception as exc:
            cycle.status="FAILED";cycle.error=str(exc);company.status=CompanyStatus.ERROR;db.add(Activity(company_id=company.id,action="COMPANY_CYCLE_FAILED",module="runtime",status="ERROR",detail=f"tick={tick}",error=str(exc)));raise
