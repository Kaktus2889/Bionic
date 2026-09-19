from sqlalchemy import select,func
from sqlalchemy.orm import Session
from .models import Goal,KPI,Task,TaskStatus,Activity,StrategyRevision,Decision,Event,Customer,Memory
class StrategyEngine:
    def bootstrap_goal(self,db:Session,company,owner)->Goal:
        existing=db.scalar(select(Goal).where(Goal.company_id==company.id,Goal.status=="ACTIVE"))
        if existing:return existing
        g=Goal(company_id=company.id,owner_id=owner.id,title=company.goal,target=100,current=0,unit="percent");db.add(g);db.flush();return g
    def signals(self,db:Session,company,kpis:dict)->dict:
        recent_mem=[m.content for m in db.scalars(select(Memory).where(Memory.company_id==company.id).order_by(Memory.created_at.desc()).limit(5))]
        return {"kpis":kpis,"critical_events":int(kpis.get("open_critical_events",0)),"churn":kpis.get("churn",0),"cash":kpis.get("cash",0),"customer_memory":recent_mem}
    def review(self,db:Session,company,kpis:dict,force:bool=False)->StrategyRevision:
        goal=db.scalar(select(Goal).where(Goal.company_id==company.id,Goal.status=="ACTIVE"));previous=db.scalar(select(StrategyRevision).where(StrategyRevision.company_id==company.id).order_by(StrategyRevision.created_at.desc()))
        sig=self.signals(db,company,kpis);problem=sig["critical_events"]>0 or sig["churn"]>=20 or (previous and kpis.get("task_completion_rate",0)<25 and company.tick_number>=3)
        new="Resolve customer and operational risks before growth" if problem else "Execute bounded experiments toward the active goal"
        reason="Critical customer/operational KPI signals require adjustment" if problem else ("Initial strategy derived from goal and current state" if not previous else "KPI signals remain within current strategy guardrails")
        if previous and previous.new_strategy==new and not force:return previous
        rev=StrategyRevision(company_id=company.id,goal_id=goal.id,reason=reason,signals=sig,previous_strategy=previous.new_strategy if previous else "",new_strategy=new,expected_effect="Improve measured goal progress while controlling risk");db.add(rev);db.flush()
        db.add(Decision(company_id=company.id,title="Strategy review",problem=reason,context={"signals":sig},options=["KEEP_STRATEGY","ADJUST_STRATEGY","CREATE_PLAN"],participants=[str(goal.owner_id)],arguments={"evidence":sig},risk="MEDIUM",expected_outcome=rev.expected_effect,final_decision="ADJUST_STRATEGY" if problem else "CREATE_PLAN",decided_by=goal.owner_id))
        db.add(Activity(company_id=company.id,agent_id=goal.owner_id,action="STRATEGY_CHANGED" if problem else "STRATEGY_REVIEWED",module="strategy_engine",detail=reason));return rev
    def evaluate(self,db:Session,company)->dict:
        total=db.scalar(select(func.count(Task.id)).where(Task.company_id==company.id)) or 0;done=db.scalar(select(func.count(Task.id)).where(Task.company_id==company.id,Task.status==TaskStatus.DONE)) or 0;progress=100*done/total if total else 0
        goal=db.scalar(select(Goal).where(Goal.company_id==company.id,Goal.status=="ACTIVE"))
        if goal:goal.current=progress
        return {"progress":progress,"tasks":total,"done":done}
