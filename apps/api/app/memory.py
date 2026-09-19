from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import Memory
class MemoryService:
    def remember(self,db:Session,company_id,agent_id,layer:str,content:str,importance:float=.5,metadata:dict|None=None,source="SYSTEM",**links)->Memory:
        m=Memory(company_id=company_id,agent_id=agent_id,layer=layer,content=content,importance=max(0,min(1,importance)),metadata_=metadata or {},source=source,**{k:v for k,v in links.items() if k in {"customer_id","event_id","task_id","decision_id","meeting_id"}});db.add(m);return m
    def remember_if_worthy(self,db:Session,company_id,agent_id,layer:str,content:str,importance:float=.5,**kw):
        if importance<.55 or len(content.strip())<8:return None
        return self.remember(db,company_id,agent_id,layer,content,importance,**kw)
    def retrieve(self,db:Session,company_id,agent_id,query:str|None=None,limit:int=8)->list[Memory]:
        limit=max(1,min(limit,20));stmt=select(Memory).where(Memory.company_id==company_id,(Memory.agent_id==agent_id)|(Memory.agent_id.is_(None)))
        rows=list(db.scalars(stmt.order_by(Memory.importance.desc(),Memory.created_at.desc()).limit(50)))
        if not query:return rows[:limit]
        terms={x.lower() for x in query.split() if len(x)>2}
        def score(m): return m.importance+sum(.12 for t in terms if t in m.content.lower())
        return sorted(rows,key=score,reverse=True)[:limit]
