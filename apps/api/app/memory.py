from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import Memory
from .embeddings import embedding_provider
class MemoryService:
    def remember(self,db:Session,company_id,agent_id,layer:str,content:str,importance:float=.5,metadata:dict|None=None,source="SYSTEM",**links)->Memory:
        m=Memory(company_id=company_id,agent_id=agent_id,layer=layer,content=content,importance=max(0,min(1,importance)),metadata_=metadata or {},source=source,embedding=embedding_provider().embed(content),**{k:v for k,v in links.items() if k in {"customer_id","event_id","task_id","decision_id","meeting_id"}});db.add(m);return m
    def remember_if_worthy(self,db:Session,company_id,agent_id,layer:str,content:str,importance:float=.5,**kw):
        if importance<.55 or len(content.strip())<8:return None
        existing=db.scalar(select(Memory).where(Memory.company_id==company_id,Memory.agent_id==agent_id,Memory.layer==layer,Memory.content==content).limit(1))
        if existing:return existing
        return self.remember(db,company_id,agent_id,layer,content,importance,**kw)
    def retrieve(self,db:Session,company_id,agent_id,query:str|None=None,limit:int=8)->list[Memory]:
        limit=max(1,min(limit,20));base=(Memory.company_id==company_id)&((Memory.agent_id==agent_id)|(Memory.agent_id.is_(None)))
        if query and db.bind and db.bind.dialect.name=="postgresql":
            vector=embedding_provider().embed(query);distance=Memory.embedding.cosine_distance(vector)
            rows=list(db.scalars(select(Memory).where(base,Memory.embedding.is_not(None)).order_by((distance-Memory.importance*.25),Memory.created_at.desc()).limit(limit)))
            if rows:return rows
        rows=list(db.scalars(select(Memory).where(base).order_by(Memory.importance.desc(),Memory.created_at.desc()).limit(50)))
        if not query:return rows[:limit]
        terms={x.lower() for x in query.split() if len(x)>2}
        return sorted(rows,key=lambda m:m.importance+sum(.12 for t in terms if t in m.content.lower()),reverse=True)[:limit]
