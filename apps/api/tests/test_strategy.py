from uuid import uuid4
from sqlalchemy import select
from app.db import SessionLocal
from app.models import Company,Agent,Goal,KPI
from app.services import bootstrap_company
from app.strategy import StrategyEngine
from app.models import Autonomy,CompanyStatus
def test_goal_strategy_bootstrap_and_evaluation():
    with SessionLocal() as db:
        c=Company(name=f"strategy-{uuid4()}",industry="SaaS",capital=1000,cash=1000,goal="Reach 100 customers",horizon_days=90,autonomy=Autonomy.SEMI_AUTONOMOUS,risk_tolerance="MEDIUM",status=CompanyStatus.PAUSED);db.add(c);db.flush();bootstrap_company(db,c);db.flush()
        g=db.scalar(select(Goal).where(Goal.company_id==c.id));assert g and g.title==c.goal
        result=StrategyEngine().evaluate(db,c);db.flush();assert result["progress"]==0
        assert db.scalar(select(KPI).where(KPI.goal_id==g.id)) is not None
