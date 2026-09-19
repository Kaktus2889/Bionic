from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import Task,TaskStatus,Agent,Activity,now
from .memory import MemoryService
class AgentRuntime:
    def step(self,db:Session,company)->dict:
        task=db.scalar(select(Task).where(Task.company_id==company.id,Task.status.in_([TaskStatus.IN_PROGRESS,TaskStatus.TODO])).order_by(Task.created_at))
        if not task:return {"acted":False}
        agent=db.get(Agent,task.assignee_id)
        MemoryService().retrieve(db,company.id,agent.id,query=task.title,limit=5)
        if task.status==TaskStatus.TODO:
            task.status=TaskStatus.IN_PROGRESS;db.add(Activity(company_id=company.id,agent_id=agent.id,action="AGENT_STARTED_TASK",module="agent_runtime",detail=task.title));return {"acted":True,"task":str(task.id),"result":"started"}
        task.status=TaskStatus.DONE;task.completed_at=now();task.actual_effort=1
        reflection=f"Completed {task.title}. Result succeeded; learned that bounded execution advances the current plan."
        MemoryService().remember_if_worthy(db,company.id,agent.id,"REFLECTION",reflection,.7,source="REFLECTION",task_id=task.id)
        db.add(Activity(company_id=company.id,agent_id=agent.id,action="AGENT_REFLECTED",module="agent_runtime",detail=reflection));return {"acted":True,"task":str(task.id),"result":"completed"}
