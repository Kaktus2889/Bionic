from dataclasses import dataclass
from sqlalchemy.orm import Session
from .models import Agent,Action,Activity,Autonomy
ROLE_PERMISSIONS={"CEO":{"READ","WRITE","CREATE_TASK","ASSIGN_TASK","MESSAGE","ACCESS_FINANCE","SPEND_MONEY","HIRE","FIRE","DEPLOY"},"CTO":{"READ","WRITE","CREATE_TASK","ASSIGN_TASK","MESSAGE","DEPLOY","RUN_CODE"},"Product Manager":{"READ","WRITE","CREATE_TASK","ASSIGN_TASK","MESSAGE"},"Developer":{"READ","WRITE","MESSAGE","RUN_CODE"},"QA Engineer":{"READ","WRITE","MESSAGE","RUN_CODE"}}
ACTION_PERMISSION={"SEND_MESSAGE":"MESSAGE","CREATE_TASK":"CREATE_TASK","SPEND_BUDGET":"SPEND_MONEY","DEPLOY":"DEPLOY","RUN_TEST":"RUN_CODE","HIRE_AGENT":"HIRE","FIRE_AGENT":"FIRE"}
HIGH_RISK={"SPEND_BUDGET","DEPLOY","FIRE_AGENT","HIRE_AGENT","DELETE_RESOURCE","MODIFY_PRODUCTION"}
class PermissionDenied(Exception): pass
class PermissionEngine:
    def check(self,agent:Agent,action_type:str)->None:
        needed=ACTION_PERMISSION.get(action_type,"WRITE")
        if needed not in ROLE_PERMISSIONS.get(agent.position,{"READ"}): raise PermissionDenied(f"{agent.position} lacks {needed}")
    def approval_required(self,autonomy:Autonomy,action_type:str,payload:dict)->bool:
        if autonomy==Autonomy.MANUAL: return True
        if autonomy==Autonomy.AUTONOMOUS: return False
        return action_type in HIGH_RISK or float(payload.get("amount",0))>=1000
class ActionEngine:
    def __init__(self,permissions:PermissionEngine|None=None): self.permissions=permissions or PermissionEngine()
    def submit(self,db:Session,company,agent:Agent,action_type:str,payload:dict)->Action:
        if agent.company_id!=company.id: raise PermissionDenied("Cross-company action denied")
        self.permissions.check(agent,action_type)
        approval=self.permissions.approval_required(company.autonomy,action_type,payload)
        a=Action(company_id=company.id,agent_id=agent.id,type=action_type,payload=payload,risk_level="HIGH" if action_type in HIGH_RISK else "LOW",requires_approval=approval,status="AWAITING_APPROVAL" if approval else "APPROVED")
        db.add(a); db.flush(); db.add(Activity(company_id=company.id,agent_id=agent.id,action=action_type,module="action_engine",status=a.status,detail=str(payload)))
        return a
