import asyncio
from uuid import uuid4
from sqlalchemy import select,func
from app.db import SessionLocal
from app.models import Company,CompanyStatus,Autonomy,Goal,Plan,Task,KPIObservation,StrategyRevision,CompanyCycle,Decision,Memory
from app.services import bootstrap_company
from app.runtime import CompanyRuntime
def make_company(db):
    c=Company(name=f"auto-{uuid4()}",industry="SaaS",capital=50000,cash=50000,goal="Acquire 100 paying customers",horizon_days=90,autonomy=Autonomy.AUTONOMOUS,risk_tolerance="MEDIUM",status=CompanyStatus.RUNNING,speed=20);db.add(c);db.flush();bootstrap_company(db,c);db.flush();return c
def test_multi_cycle_autonomy_feedback_loop():
    with SessionLocal() as db:
        c=make_company(db);cid=c.id
        for _ in range(7):asyncio.run(CompanyRuntime().cycle(db,c));db.commit()
        assert c.tick_number==7
        assert db.scalar(select(func.count(Plan.id)).where(Plan.company_id==cid))>=2
        assert db.scalar(select(func.count(Task.id)).where(Task.company_id==cid))>=6
        assert db.scalar(select(func.count(KPIObservation.id)).where(KPIObservation.company_id==cid))>=70
        assert db.scalar(select(func.count(StrategyRevision.id)).where(StrategyRevision.company_id==cid))>=2
        assert db.scalar(select(func.count(Decision.id)).where(Decision.company_id==cid))>=2
        assert db.scalar(select(func.count(Memory.id)).where(Memory.company_id==cid,Memory.layer=="REFLECTION"))>=1
def test_cycle_recovery_is_idempotent():
    with SessionLocal() as db:
        c=make_company(db);cid=c.id;key=f"{cid}:1";db.add(CompanyCycle(company_id=cid,tick=1,idempotency_key=key,status="RUNNING",phase="PLAN"));db.commit()
        asyncio.run(CompanyRuntime().cycle(db,c));db.commit()
        tasks=db.scalar(select(func.count(Task.id)).where(Task.company_id==cid));decisions=db.scalar(select(func.count(Decision.id)).where(Decision.company_id==cid));plans=db.scalar(select(func.count(Plan.id)).where(Plan.company_id==cid))
        cycle=asyncio.run(CompanyRuntime().cycle(db,c));db.commit()
        assert cycle.tick==2
        assert db.scalar(select(func.count(Plan.id)).where(Plan.company_id==cid))==plans
        assert db.scalar(select(func.count(Task.id)).where(Task.company_id==cid))==tasks
        assert db.scalar(select(func.count(Decision.id)).where(Decision.company_id==cid))==decisions
