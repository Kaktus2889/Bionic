from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import Customer,CustomerInteraction,CustomerNote
from .memory import MemoryService
class CustomerService:
    def create(self,db:Session,company,name:str,assigned_agent_id=None,segment="default",context=None)->Customer:
        c=Customer(company_id=company.id,name=name,assigned_agent_id=assigned_agent_id,segment=segment,context=context or {});db.add(c);db.flush();return c
    def interact(self,db:Session,customer:Customer,agent_id,content:str,channel="email",direction="INBOUND")->CustomerInteraction:
        x=CustomerInteraction(customer_id=customer.id,agent_id=agent_id,channel=channel,direction=direction,content=content);db.add(x)
        MemoryService().remember_if_worthy(db,customer.company_id,agent_id,"CUSTOMER",content,.7,source="CUSTOMER",customer_id=customer.id)
        return x
    def context(self,db:Session,customer_id,limit=10)->dict:
        c=db.get(Customer,customer_id)
        interactions=list(db.scalars(select(CustomerInteraction).where(CustomerInteraction.customer_id==customer_id).order_by(CustomerInteraction.created_at.desc()).limit(limit)))
        notes=list(db.scalars(select(CustomerNote).where(CustomerNote.customer_id==customer_id).order_by(CustomerNote.created_at.desc()).limit(limit)))
        return {"customer":c,"interactions":interactions,"notes":notes}
