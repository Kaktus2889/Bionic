from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import Event,Agent,Task,Priority,TaskStatus,Activity
from .memory import MemoryService
class EventEngine:
    ROUTES={"CUSTOMER_COMPLAINT":"Support","NEW_LEAD":"Sales","PAYMENT_FAILURE":"CFO","SECURITY_INCIDENT":"CTO","CRITICAL_BUG":"CTO"}
    def create(self,db:Session,company,event_type:str,payload:dict,idempotency_key:str,customer_id=None,source="INTERNAL",priority="MEDIUM")->Event:
        old=db.scalar(select(Event).where(Event.company_id==company.id,Event.idempotency_key==idempotency_key))
        if old:return old
        e=Event(company_id=company.id,type=event_type,payload=payload,idempotency_key=idempotency_key,customer_id=customer_id,source=source,priority=priority);db.add(e);db.flush();return e
    def process(self,db:Session,event:Event)->Event:
        if event.status=="PROCESSED":return event
        event.status="PROCESSING";event.attempts+=1
        try:
            role=self.ROUTES.get(event.type,"CEO")
            agent=db.scalar(select(Agent).where(Agent.company_id==event.company_id,Agent.position==role))
            if not agent: agent=db.scalar(select(Agent).where(Agent.company_id==event.company_id).order_by(Agent.permission_level.desc()))
            event.agent_id=agent.id
            MemoryService().remember_if_worthy(db,event.company_id,agent.id,"EVENT",f"{event.type}: {event.payload}",.75,source="EVENT",event_id=event.id,customer_id=event.customer_id)
            task=Task(company_id=event.company_id,title=f"Respond to {event.type}",description=str(event.payload),creator_id=agent.id,assignee_id=agent.id,priority=Priority.CRITICAL if event.priority=="CRITICAL" else Priority.HIGH,status=TaskStatus.TODO);db.add(task)
            db.add(Activity(company_id=event.company_id,agent_id=agent.id,action="EVENT_ROUTED",module="event_engine",detail=f"{event.type} -> {agent.position}"))
            event.status="PROCESSED"; from .models import now; event.processed_at=now(); return event
        except Exception as exc:
            event.error=str(exc);event.status="FAILED" if event.attempts>=event.max_retries else "PENDING";raise
