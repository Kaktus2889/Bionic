from uuid import UUID
from fastapi import FastAPI,Depends,HTTPException,WebSocket,WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select,func
from sqlalchemy.orm import Session
from .config import settings
from .db import get_db
from .models import Company,Agent,Task,Message,Decision,Activity,CompanyStatus,Autonomy,Customer,Event,Meeting,Action,Goal,StrategyRevision,Plan,KPI,KPIObservation,CompanyCycle,AgentDecisionTrace,ActionResult,InformationRequest
from .schemas import CompanyCreate,CompanyOut,TickOut
from .services import bootstrap_company,run_tick
from .finance import FinanceEngine
from .memory import MemoryService
from .customers import CustomerService
from .events import EventEngine
from .meetings import MeetingEngine
from .actions import ActionEngine,InvalidTransition
from .queue import ActionQueue
from .strategy import StrategyEngine
from .runtime import CompanyRuntime
app=FastAPI(title="AI COMPANY OS",version="0.1.0")
app.add_middleware(CORSMiddleware,allow_origins=[x.strip() for x in settings.cors_origins.split(",")],allow_methods=["*"],allow_headers=["*"])
def get_company(db:Session,id:UUID):
    c=db.get(Company,id)
    if not c: raise HTTPException(404,"Company not found")
    return c
@app.get("/health")
def health(): return {"status":"ok"}
@app.post("/companies",response_model=CompanyOut,status_code=201)
def create_company(body:CompanyCreate,db:Session=Depends(get_db)):
    try: autonomy=Autonomy(body.autonomy)
    except ValueError as e: raise HTTPException(422,"Invalid autonomy") from e
    c=Company(name=body.name,industry=body.industry,capital=body.capital,cash=body.capital,goal=body.goal,horizon_days=body.horizon_days,autonomy=autonomy,risk_tolerance=body.risk_tolerance,status=CompanyStatus.PAUSED)
    db.add(c); db.flush(); bootstrap_company(db,c); db.commit(); db.refresh(c); return c
@app.get("/companies/{id}",response_model=CompanyOut)
def company(id:UUID,db:Session=Depends(get_db)): return get_company(db,id)
@app.post("/companies/{id}/start",response_model=CompanyOut)
def start(id:UUID,db:Session=Depends(get_db)):
    c=get_company(db,id); c.status=CompanyStatus.RUNNING; db.commit(); db.refresh(c); return c
@app.post("/companies/{id}/pause",response_model=CompanyOut)
def pause(id:UUID,db:Session=Depends(get_db)):
    c=get_company(db,id); c.status=CompanyStatus.PAUSED; db.commit(); db.refresh(c); return c
@app.post("/companies/{id}/tick")
async def tick(id:UUID,db:Session=Depends(get_db)):
    c=get_company(db,id)
    if c.status==CompanyStatus.PAUSED:raise HTTPException(409,"Company is paused")
    cycle=await CompanyRuntime().cycle(db,c);db.commit();tasks_n=db.scalar(select(func.count(Task.id)).where(Task.company_id==id)) or 0;messages_n=db.scalar(select(func.count(Message.id)).where(Message.company_id==id)) or 0;decisions_n=db.scalar(select(func.count(Decision.id)).where(Decision.company_id==id)) or 0;activities_n=db.scalar(select(func.count(Activity.id)).where(Activity.company_id==id)) or 0;return {"tick":cycle.tick,"status":cycle.status,"phase":cycle.phase,"tasks_created":tasks_n,"messages_created":messages_n,"decisions_created":decisions_n,"activities":activities_n}
@app.get("/companies/{id}/agents")
def agents(id:UUID,db:Session=Depends(get_db)):
    get_company(db,id); return db.scalars(select(Agent).where(Agent.company_id==id)).all()
@app.get("/companies/{id}/tasks")
def tasks(id:UUID,db:Session=Depends(get_db)): get_company(db,id); return db.scalars(select(Task).where(Task.company_id==id).order_by(Task.created_at.desc())).all()
@app.get("/companies/{id}/messages")
def messages(id:UUID,db:Session=Depends(get_db)): get_company(db,id); return db.scalars(select(Message).where(Message.company_id==id).order_by(Message.created_at.desc())).all()
@app.get("/companies/{id}/decisions")
def decisions(id:UUID,db:Session=Depends(get_db)): get_company(db,id); return db.scalars(select(Decision).where(Decision.company_id==id).order_by(Decision.created_at.desc())).all()
@app.get("/companies/{id}/activity")
def activity(id:UUID,db:Session=Depends(get_db)): get_company(db,id); return db.scalars(select(Activity).where(Activity.company_id==id).order_by(Activity.created_at.desc()).limit(100)).all()

@app.get("/companies/{id}/finance")
def finance(id:UUID,db:Session=Depends(get_db)): get_company(db,id); return FinanceEngine().summary(db,id)
@app.get("/companies/{id}/memory")
def memory(id:UUID,db:Session=Depends(get_db)): get_company(db,id); return MemoryService().retrieve(db,id,None)
@app.websocket("/ws/companies/{id}/activity")
async def activity_ws(ws:WebSocket,id:UUID):
    await ws.accept()
    try:
        last=None
        while True:
            with next(get_db()) as db:
                rows=list(db.scalars(select(Activity).where(Activity.company_id==id).order_by(Activity.created_at.desc()).limit(20)))
            marker=str(rows[0].id) if rows else None
            if marker!=last:
                await ws.send_json([{"id":str(x.id),"action":x.action,"detail":x.detail,"status":x.status,"created_at":x.created_at.isoformat()} for x in reversed(rows)])
                last=marker
            import asyncio; await asyncio.sleep(1)
    except WebSocketDisconnect: return

@app.post("/companies/{id}/customers",status_code=201)
def create_customer(id:UUID,body:dict,db:Session=Depends(get_db)):
    c=get_company(db,id);x=CustomerService().create(db,c,body["name"],body.get("assigned_agent_id"),body.get("segment","default"),body.get("context"));db.commit();db.refresh(x);return x
@app.get("/companies/{id}/customers")
def customers(id:UUID,db:Session=Depends(get_db)):get_company(db,id);return db.scalars(select(Customer).where(Customer.company_id==id)).all()
@app.post("/companies/{id}/events",status_code=201)
def create_event(id:UUID,body:dict,db:Session=Depends(get_db)):
    c=get_company(db,id);e=EventEngine().create(db,c,body["type"],body.get("payload",{}),body["idempotency_key"],body.get("customer_id"),body.get("source","API"),body.get("priority","MEDIUM"));EventEngine().process(db,e);db.commit();db.refresh(e);return e
@app.get("/companies/{id}/events")
def events(id:UUID,db:Session=Depends(get_db)):get_company(db,id);return db.scalars(select(Event).where(Event.company_id==id).order_by(Event.created_at.desc())).all()
@app.post("/companies/{id}/meetings",status_code=201)
def create_meeting(id:UUID,body:dict,db:Session=Depends(get_db)):
    c=get_company(db,id);owner=db.get(Agent,body["owner_id"]);parts=list(db.scalars(select(Agent).where(Agent.id.in_(body["participant_ids"]))));m=MeetingEngine().create(db,c,owner,parts,body["agenda"],body.get("type","REVIEW"),body.get("context"));db.commit();db.refresh(m);return m
@app.post("/meetings/{id}/execute")
def execute_meeting(id:UUID,db:Session=Depends(get_db)):
    m=db.get(Meeting,id)
    if not m:raise HTTPException(404,"Meeting not found")
    d=MeetingEngine().execute(db,m);db.commit();return d
@app.get("/companies/{id}/meetings")
def meetings(id:UUID,db:Session=Depends(get_db)):get_company(db,id);return db.scalars(select(Meeting).where(Meeting.company_id==id).order_by(Meeting.created_at.desc())).all()
@app.post("/companies/{id}/actions",status_code=201)
def create_action(id:UUID,body:dict,db:Session=Depends(get_db)):
    c=get_company(db,id);agent=db.get(Agent,body["agent_id"]);a=ActionEngine().submit(db,c,agent,body["type"],body.get("payload",{}),body.get("idempotency_key"));db.commit();db.refresh(a);return a
@app.post("/actions/{id}/approve")
def approve_action(id:UUID,body:dict,db:Session=Depends(get_db)):
    a=db.get(Action,id)
    if not a:raise HTTPException(404,"Action not found")
    try:
        ActionEngine().approve(db,a,db.get(Agent,body["approver_id"]));ActionEngine().queue(db,a);db.commit();ActionQueue().enqueue(a.id);db.refresh(a);return a
    except InvalidTransition as e:db.rollback();raise HTTPException(409,str(e)) from e
@app.get("/companies/{id}/actions")
def actions(id:UUID,db:Session=Depends(get_db)):get_company(db,id);return db.scalars(select(Action).where(Action.company_id==id).order_by(Action.created_at.desc())).all()

@app.get("/companies/{id}/strategy")
def strategy(id:UUID,db:Session=Depends(get_db)):return StrategyEngine().evaluate(db,get_company(db,id))

@app.post("/companies/{id}/speed")
def set_speed(id:UUID,body:dict,db:Session=Depends(get_db)):
    c=get_company(db,id);speed=int(body.get("speed",1))
    if speed not in {1,5,20,100}:raise HTTPException(422,"speed must be 1, 5, 20 or 100")
    c.speed=speed;db.commit();return {"speed":speed}
@app.get("/companies/{id}/autonomous-loop")
def autonomous_loop(id:UUID,db:Session=Depends(get_db)):
    c=get_company(db,id)
    goal=db.scalar(select(Goal).where(Goal.company_id==id,Goal.status=="ACTIVE"))
    strategy=db.scalar(select(StrategyRevision).where(StrategyRevision.company_id==id).order_by(StrategyRevision.created_at.desc()))
    plans=list(db.scalars(select(Plan).where(Plan.company_id==id).order_by(Plan.created_at.desc()).limit(5)))
    kpis=list(db.scalars(select(KPI).where(KPI.company_id==id)))
    observations=list(db.scalars(select(KPIObservation).where(KPIObservation.company_id==id).order_by(KPIObservation.created_at.desc()).limit(50)))
    cycles=list(db.scalars(select(CompanyCycle).where(CompanyCycle.company_id==id).order_by(CompanyCycle.tick.desc()).limit(20)))
    timeline=list(db.scalars(select(Activity).where(Activity.company_id==id).order_by(Activity.created_at.desc()).limit(50)))
    return {"company":{"status":c.status,"speed":c.speed,"tick":c.tick_number},"goal":goal,"strategy":strategy,"plans":plans,"kpis":kpis,"observations":observations,"cycles":cycles,"timeline":timeline}

@app.get("/companies/{id}/agent-live")
def agent_live(id:UUID,db:Session=Depends(get_db)):
    get_company(db,id);rows=list(db.scalars(select(AgentDecisionTrace).where(AgentDecisionTrace.company_id==id).order_by(AgentDecisionTrace.created_at.desc()).limit(30)))
    return rows
@app.get("/agents/{id}/decision-traces")
def decision_traces(id:UUID,db:Session=Depends(get_db)):
    return list(db.scalars(select(AgentDecisionTrace).where(AgentDecisionTrace.agent_id==id).order_by(AgentDecisionTrace.created_at.desc()).limit(50)))
