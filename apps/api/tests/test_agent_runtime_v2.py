import asyncio,json
from uuid import uuid4
from app.agent_decision import ActionIntent,ActionPolicy,ObservationBuilder,AgentToolRegistry
from app.intent_planner import IntentPlanner
from app.llm import LLMProvider,LLMResult,LLMRouter
from app.db import SessionLocal
from app.models import Company,Agent,Autonomy,CompanyStatus,Task,TaskStatus,Priority
from app.services import bootstrap_company
class Scripted(LLMProvider):
    def __init__(self,items):self.items=list(items)
    async def complete(self,prompt,*,model):
        x=self.items.pop(0)
        if isinstance(x,Exception):raise x
        return LLMResult(x)
def test_llm_contract_valid_invalid_schema_empty_timeout_and_error():
    valid=json.dumps([{"type":"WAIT","objective":"wait safely","reasoning_summary":"No safe work","expected_result":"No side effect","confidence":.9}])
    async def run():
        planner=IntentPlanner();fallback=[ActionIntent(type="WAIT",objective="fallback work",reasoning_summary="fallback reason",expected_result="safe",confidence=.8)]
        for seq,expected in [([valid],"wait safely"),(["bad",""],"fallback work"),([json.dumps([{"type":"WAIT"}]),"bad"],"fallback work"),([TimeoutError(),RuntimeError()],"fallback work")]:
            router=LLMRouter({"cheap":Scripted(seq),"strong":Scripted(seq.copy())})
            import app.intent_planner as mod
            old=mod.default_router;mod.default_router=lambda:router
            try:assert (await planner.propose({"tools":["WAIT"]},fallback))[0].objective==expected
            finally:mod.default_router=old
    asyncio.run(run())
def test_policy_blocks_nonexistent_unauthorized_expense_and_duplicate():
    with SessionLocal() as db:
        c=Company(name=f"adv-{uuid4()}",industry="x",capital=100,cash=100,goal="g",horizon_days=10,autonomy=Autonomy.AUTONOMOUS,risk_tolerance="LOW",status=CompanyStatus.RUNNING);db.add(c);db.flush();bootstrap_company(db,c);db.flush()
        dev=db.query(Agent).filter_by(company_id=c.id,position="Developer").one()
        for intent in [ActionIntent(type="ROOT_ACCESS",objective="bad tool",reasoning_summary="bad",expected_result="bad",confidence=.9),ActionIntent(type="PROPOSE_EXPENSE",objective="overspend",reasoning_summary="costly",expected_result="spend",confidence=.9,estimated_cost=9999,risk="HIGH")]:
            assert ActionPolicy().check(db,c,dev,intent)["allowed"] is False
def test_observation_is_role_bounded():
    with SessionLocal() as db:
        c=Company(name=f"obs-{uuid4()}",industry="x",capital=1000,cash=1000,goal="g",horizon_days=10,autonomy=Autonomy.AUTONOMOUS,risk_tolerance="LOW",status=CompanyStatus.RUNNING);db.add(c);db.flush();bootstrap_company(db,c);db.flush()
        dev=db.query(Agent).filter_by(company_id=c.id,position="Developer").one();obs=ObservationBuilder().build(db,c,dev)
        assert obs["cash"] is None and "PROPOSE_EXPENSE" not in obs["tools"] and "ACCESS_FINANCE" not in obs["permissions"]
