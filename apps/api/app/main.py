from uuid import UUID
from fastapi import FastAPI,Depends,HTTPException,WebSocket,WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select,func
from sqlalchemy.orm import Session
from .config import settings
from .db import get_db
from .models import Company,Agent,Task,Message,Decision,Activity,CompanyStatus,Autonomy
from .schemas import CompanyCreate,CompanyOut,TickOut
from .services import bootstrap_company,run_tick
from .finance import FinanceEngine
from .memory import MemoryService
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
    c=get_company(db,id); c.status=CompanyStatus.REALTIME; db.commit(); db.refresh(c); return c
@app.post("/companies/{id}/pause",response_model=CompanyOut)
def pause(id:UUID,db:Session=Depends(get_db)):
    c=get_company(db,id); c.status=CompanyStatus.PAUSED; db.commit(); db.refresh(c); return c
@app.post("/companies/{id}/tick",response_model=TickOut)
def tick(id:UUID,db:Session=Depends(get_db)):
    c=get_company(db,id)
    try: n,t,m,d=run_tick(db,c); db.commit()
    except ValueError as e: db.rollback(); raise HTTPException(409,str(e)) from e
    count=db.scalar(select(func.count(Activity.id)).where(Activity.company_id==id)) or 0
    return TickOut(tick=n,activities=count,tasks_created=t,messages_created=m,decisions_created=d)
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
