from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import Memory
class MemoryService:
    def remember(self,db:Session,company_id,agent_id,layer:str,content:str,importance:float=.5,metadata:dict|None=None)->Memory:
        m=Memory(company_id=company_id,agent_id=agent_id,layer=layer,content=content,importance=max(0,min(1,importance)),metadata_=metadata or {}); db.add(m); return m
    def retrieve(self,db:Session,company_id,agent_id,limit:int=8)->list[Memory]:
        stmt=select(Memory).where(Memory.company_id==company_id,(Memory.agent_id==agent_id)|(Memory.agent_id.is_(None))).order_by(Memory.importance.desc(),Memory.created_at.desc()).limit(limit)
        return list(db.scalars(stmt))
