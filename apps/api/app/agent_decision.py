from dataclasses import dataclass
from typing import Any
from pydantic import BaseModel,Field
from sqlalchemy import select,func
from sqlalchemy.orm import Session
from .models import Agent,Task,TaskStatus,Message,Event,KPI,Action,ActionResult,InformationRequest,CompanyAccount
from .actions import ROLE_PERMISSIONS,PermissionEngine
from .memory import MemoryService
class ActionIntent(BaseModel):
    type:str; objective:str=Field(min_length=3,max_length=300); reasoning_summary:str=Field(min_length=3,max_length=500); expected_result:str=Field(min_length=2,max_length=300); confidence:float=Field(ge=0,le=1); priority:str="MEDIUM"; target:str|None=None; parameters:dict[str,Any]={}; estimated_cost:float=Field(default=0,ge=0); risk:str="LOW"
class AgentReflection(BaseModel):
    outcome:str; success:bool; lesson:str; unexpected_result:str|None=None; memory_candidate:str|None=None; strategy_signal:str|None=None; follow_up_needed:bool=False
@dataclass(frozen=True)
class ToolSpec:
    name:str;description:str;required_permissions:set[str];risk_level:str
class AgentToolRegistry:
    SPECS={
      "WORK_ON_TASK":ToolSpec("WORK_ON_TASK","Advance an assigned task",{"WRITE"},"LOW"),"SEND_MESSAGE":ToolSpec("SEND_MESSAGE","Send role-scoped message",{"MESSAGE"},"LOW"),"REQUEST_INFORMATION":ToolSpec("REQUEST_INFORMATION","Ask another agent for missing evidence",{"MESSAGE"},"LOW"),"CREATE_TASK":ToolSpec("CREATE_TASK","Delegate bounded work",{"CREATE_TASK"},"LOW"),"PROPOSE_TASK":ToolSpec("PROPOSE_TASK","Propose bounded work",{"WRITE"},"LOW"),"UPDATE_TASK":ToolSpec("UPDATE_TASK","Update assigned task state",{"WRITE"},"LOW"),"REQUEST_REVIEW":ToolSpec("REQUEST_REVIEW","Request peer review",{"MESSAGE"},"LOW"),"PROPOSE_DECISION":ToolSpec("PROPOSE_DECISION","Propose a decision",{"WRITE"},"MEDIUM"),"CALL_MEETING":ToolSpec("CALL_MEETING","Call a meeting",{"MESSAGE"},"MEDIUM"),"CONTACT_CUSTOMER":ToolSpec("CONTACT_CUSTOMER","Contact assigned customer",{"WRITE"},"MEDIUM"),"PROPOSE_EXPENSE":ToolSpec("PROPOSE_EXPENSE","Propose financial spend",{"SPEND_MONEY"},"HIGH"),"ESCALATE":ToolSpec("ESCALATE","Escalate to manager",{"MESSAGE"},"LOW"),"WAIT":ToolSpec("WAIT","Take no side effect",{"READ"},"LOW")}
    def available(self,agent): 
        perms=ROLE_PERMISSIONS.get(agent.position,{"READ"});return [s for s in self.SPECS.values() if s.required_permissions<=perms]
class ObservationBuilder:
    def build(self,db:Session,company,agent:Agent)->dict:
        tasks=list(db.scalars(select(Task).where(Task.company_id==company.id,Task.assignee_id==agent.id,Task.status.notin_([TaskStatus.DONE,TaskStatus.CANCELLED])).limit(8)))
        query=" ".join(t.title for t in tasks) or agent.position;mem=MemoryService().retrieve(db,company.id,agent.id,query=query,limit=5)
        kpis=list(db.scalars(select(KPI).where(KPI.company_id==company.id).limit(8))) if agent.permission_level>=3 else list(db.scalars(select(KPI).where(KPI.company_id==company.id,KPI.name=="task_completion_rate").limit(3)))
        events=list(db.scalars(select(Event).where(Event.company_id==company.id,Event.status!="PROCESSED").order_by(Event.created_at.desc()).limit(5))) if agent.permission_level>=3 else []
        results=list(db.scalars(select(ActionResult).where(ActionResult.agent_id==agent.id).order_by(ActionResult.created_at.desc()).limit(5)))
        requests=list(db.scalars(select(InformationRequest).where(InformationRequest.recipient_id==agent.id,InformationRequest.status=="OPEN").limit(5)))
        cash=None
        if "ACCESS_FINANCE" in ROLE_PERMISSIONS.get(agent.position,set()):cash=db.scalar(select(CompanyAccount.balance).where(CompanyAccount.company_id==company.id))
        return {"identity":{"id":str(agent.id),"name":agent.name,"role":agent.position,"department":agent.department},"goals":agent.goals[:5],"tasks":[{"id":str(t.id),"title":t.title,"status":t.status.value,"parent":str(t.parent_task_id) if t.parent_task_id else None,"dependencies":t.dependencies} for t in tasks],"memories":[{"layer":m.layer,"content":m.content,"importance":m.importance} for m in mem],"kpis":[{"id":str(k.id),"name":k.name,"value":k.value,"target":k.target} for k in kpis],"events":[{"id":str(e.id),"type":e.type,"priority":e.priority} for e in events],"tools":[s.name for s in AgentToolRegistry().available(agent)],"permissions":sorted(ROLE_PERMISSIONS.get(agent.position,{"READ"})),"cash":cash,"recent_results":[{"status":r.status,"summary":r.output_summary,"error":r.error} for r in results],"information_requests":[{"id":str(x.id),"objective":x.objective,"question":x.question} for x in requests]}
class ActionEvaluator:
    def score(self,intent:ActionIntent,observation:dict)->float:
        score=.35*intent.confidence+.2*(intent.priority in {"HIGH","CRITICAL"})+.2*(intent.type in observation["tools"])-.15*min(intent.estimated_cost/1000,1)-.1*(intent.risk=="HIGH")
        failures=sum(1 for r in observation["recent_results"] if r["status"]=="FAILED" and intent.type in r["summary"]);return score-.2*failures
    def choose(self,candidates:list[ActionIntent],obs:dict)->ActionIntent:return max(candidates,key=lambda x:self.score(x,obs))
class ActionPolicy:
    def check(self,db:Session,company,agent,intent:ActionIntent)->dict:
        exists=intent.type in AgentToolRegistry.SPECS;allowed=intent.type in {x.name for x in AgentToolRegistry().available(agent)}
        duplicate=db.scalar(select(func.count(Action.id)).where(Action.company_id==company.id,Action.agent_id==agent.id,Action.type==intent.type,Action.status.in_(["APPROVED","QUEUED","EXECUTING"]))) or 0
        budget_ok=intent.estimated_cost<=company.cash;low_confidence=intent.confidence<.45 and intent.risk in {"MEDIUM","HIGH"}
        return {"tool_exists":exists,"role_allowed":allowed,"budget_ok":budget_ok,"not_duplicate":duplicate==0,"confidence_safe":not low_confidence,"allowed":exists and allowed and budget_ok and duplicate==0 and not low_confidence}
