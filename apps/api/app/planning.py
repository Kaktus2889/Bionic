import asyncio,json
from pydantic import BaseModel,Field,ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session
from .config import settings
from .llm import default_router
from .models import Plan,Task,TaskStatus,Priority,Agent,Activity
class PlanStep(BaseModel):
    title:str=Field(min_length=4,max_length=180); owner_role:str=Field(min_length=2,max_length=80); priority:str="MEDIUM"
class PlanProposal(BaseModel):
    objective:str=Field(min_length=5,max_length=500); steps:list[PlanStep]=Field(min_length=1,max_length=6); expected_outcome:str=Field(min_length=5,max_length=500)
class PlanningEngine:
    async def propose(self,context:dict)->PlanProposal:
        prompt="Return JSON plan only. Context: "+json.dumps(context,default=str)[:7000]
        router=default_router()
        for _ in range(2):
            result=await router.route("PLANNING",prompt)
            try:return PlanProposal.model_validate_json(result.text)
            except ValidationError:prompt+=" Previous response invalid; obey schema with objective, steps(title,owner_role,priority), expected_outcome."
        return PlanProposal(objective="Stabilize measurable execution",steps=[PlanStep(title="Review current company signals",owner_role="CEO"),PlanStep(title="Execute highest priority improvement",owner_role="Developer"),PlanStep(title="Verify KPI impact",owner_role="QA Engineer")],expected_outcome="Validated progress")
    async def create(self,db:Session,company,goal,strategy,signals:dict,cycle_key:str)->Plan:
        old=db.scalar(select(Plan).where(Plan.company_id==company.id,Plan.cycle_key==cycle_key))
        if old:return old
        proposal=await self.propose({"goal":goal.title,"strategy":strategy.new_strategy,"signals":signals})
        steps=proposal.steps[:settings.max_plan_steps];agents={a.position:a for a in db.scalars(select(Agent).where(Agent.company_id==company.id))}
        plan=Plan(company_id=company.id,goal_id=goal.id,strategy_id=strategy.id,objective=proposal.objective,steps=[x.model_dump() for x in steps],owners=[x.owner_role for x in steps],dependencies={},priority="HIGH",expected_outcome=proposal.expected_outcome,cycle_key=cycle_key);db.add(plan);db.flush()
        for i,step in enumerate(steps):
            owner=agents.get(step.owner_role) or agents.get("CEO");key=f"plan:{plan.id}:step:{i}"
            existing=db.scalar(select(Task).where(Task.company_id==company.id,Task.description.contains(key)))
            if not existing:db.add(Task(company_id=company.id,title=step.title,description=f"{proposal.objective}\n[{key}]",creator_id=agents["CEO"].id,assignee_id=owner.id,priority=Priority(step.priority if step.priority in Priority._value2member_map_ else "MEDIUM"),status=TaskStatus.TODO,dependencies=[] if i==0 else [i-1]))
        db.add(Activity(company_id=company.id,agent_id=agents["CEO"].id,action="PLAN_CREATED",module="planning",detail=f"{plan.id}: {proposal.objective}"));return plan
