from uuid import uuid4
from fastapi.testclient import TestClient
from redis import Redis
from sqlalchemy import select
from app.main import app
from app.db import SessionLocal
from app.models import Company,Agent,Customer,Event,Meeting,Action,Activity,Transaction,Memory
from app.customers import CustomerService
from app.events import EventEngine
from app.meetings import MeetingEngine
from app.actions import ActionEngine,InvalidTransition
from app.queue import ActionQueue
from app.finance import FinanceEngine
client=TestClient(app)
def test_autonomous_company_loop():
    payload={"name":f"Loop-{uuid4()}","industry":"SaaS","capital":50000,"goal":"Reach paying customers","horizon_days":90,"autonomy":"SEMI_AUTONOMOUS","risk_tolerance":"MEDIUM"}
    cid=client.post("/companies",json=payload).json()["id"]
    with SessionLocal() as db:
        company=db.get(Company,cid);agents=list(db.scalars(select(Agent).where(Agent.company_id==company.id)));ceo=next(a for a in agents if a.position=="CEO")
        customer=CustomerService().create(db,company,"Acme Customer",ceo.id,"SMB",{"need":"reliability"});CustomerService().interact(db,customer,ceo.id,"Critical onboarding problem blocks purchase")
        event=EventEngine().create(db,company,"CUSTOMER_COMPLAINT",{"message":"onboarding blocked"},f"evt-{uuid4()}",customer.id,priority="CRITICAL");EventEngine().process(db,event)
        meeting=MeetingEngine().create(db,company,ceo,agents[:3],"Resolve onboarding complaint",context={"customer_id":str(customer.id)});decision=MeetingEngine().execute(db,meeting)
        action=ActionEngine().submit(db,company,ceo,"SPEND_BUDGET",{"amount":1500,"category":"CUSTOMER_SUCCESS","description":"Onboarding remediation"},f"act-{uuid4()}")
        assert action.status=="AWAITING_APPROVAL"
        try:ActionEngine().queue(db,action);assert False
        except InvalidTransition:pass
        ActionEngine().approve(db,action,ceo);ActionEngine().queue(db,action);db.commit();action_id=action.id
        assert len(__import__("app.memory",fromlist=["MemoryService"]).MemoryService().retrieve(db,company.id,ceo.id,query="onboarding",limit=5))<=5
    redis=Redis.from_url("redis://localhost:6379/0",decode_responses=True);queue=ActionQueue(redis);queue.enqueue(action_id);queued=queue.pop(2);assert queued==str(action_id)
    with SessionLocal() as db:
        action=db.get(Action,queued);ActionEngine().execute(db,action);db.commit()
        assert action.status=="SUCCEEDED"
        assert db.scalar(select(Transaction).where(Transaction.reference_id==action.id)) is not None
        assert FinanceEngine().summary(db,action.company_id)["cash"]==48500
        assert db.scalar(select(Activity).where(Activity.company_id==action.company_id,Activity.action=="ACTION_SUCCEEDED")) is not None
        assert db.scalar(select(Memory).where(Memory.company_id==action.company_id,Memory.customer_id.is_not(None))) is not None
    with client.websocket_connect(f"/ws/companies/{cid}/activity") as ws:
        rows=ws.receive_json();assert any(x["action"]=="ACTION_SUCCEEDED" for x in rows)
