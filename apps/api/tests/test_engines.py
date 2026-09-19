from app.db import SessionLocal
from app.models import Company,Agent,Autonomy,CompanyStatus
from app.actions import PermissionEngine,PermissionDenied
from app.finance import FinanceEngine
from app.memory import MemoryService
def make(db):
    c=Company(name="x",industry="x",capital=1000,cash=1000,goal="g",horizon_days=30,autonomy=Autonomy.SEMI_AUTONOMOUS,risk_tolerance="MEDIUM",status=CompanyStatus.PAUSED); db.add(c); db.flush()
    a=Agent(company_id=c.id,name="dev",position="Developer",department="Engineering"); db.add(a); db.flush(); FinanceEngine().open_account(db,c); return c,a
def test_permissions_and_finance_memory():
    with SessionLocal() as db:
        c,a=make(db)
        try: PermissionEngine().check(a,"SPEND_BUDGET"); assert False
        except PermissionDenied: pass
        FinanceEngine().record(db,c,"DEBIT",100,"TOOLS","CI test",True)
        assert FinanceEngine().summary(db,c.id)["cash"]==900
        MemoryService().remember(db,c.id,a.id,"LONG_TERM","important",.9)
        db.flush(); assert MemoryService().retrieve(db,c.id,a.id)[0].content=="important"
