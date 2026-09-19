from sqlalchemy import select,func
from sqlalchemy.orm import Session
from .models import Goal,KPI,Task,TaskStatus,Activity
class StrategyEngine:
    def bootstrap_goal(self,db:Session,company,owner)->Goal:
        existing=db.scalar(select(Goal).where(Goal.company_id==company.id,Goal.status=="ACTIVE"))
        if existing:return existing
        g=Goal(company_id=company.id,owner_id=owner.id,title=company.goal,target=100,current=0,unit="percent");db.add(g);db.flush();db.add(KPI(company_id=company.id,agent_id=owner.id,goal_id=g.id,name="Task completion",value=0,target=100,unit="percent"));return g
    def evaluate(self,db:Session,company)->dict:
        total=db.scalar(select(func.count(Task.id)).where(Task.company_id==company.id)) or 0;done=db.scalar(select(func.count(Task.id)).where(Task.company_id==company.id,Task.status==TaskStatus.DONE)) or 0;progress=100*done/total if total else 0
        goal=db.scalar(select(Goal).where(Goal.company_id==company.id,Goal.status=="ACTIVE"))
        if goal:goal.current=progress;db.add(KPI(company_id=company.id,goal_id=goal.id,name="Task completion",value=progress,target=100,unit="percent"))
        db.add(Activity(company_id=company.id,agent_id=goal.owner_id if goal else None,action="STRATEGY_EVALUATED",module="strategy_engine",detail=f"progress={progress:.1f}%"));return {"progress":progress,"tasks":total,"done":done}
