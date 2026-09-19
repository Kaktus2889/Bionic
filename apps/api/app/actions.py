from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import Agent,Action,ActionAttempt,Activity,Autonomy,Task,TaskStatus,Priority,now
ROLE_PERMISSIONS={"CEO":{"READ","WRITE","CREATE_TASK","ASSIGN_TASK","MESSAGE","ACCESS_FINANCE","SPEND_MONEY","HIRE","FIRE","DEPLOY"},"CTO":{"READ","WRITE","CREATE_TASK","ASSIGN_TASK","MESSAGE","DEPLOY","RUN_CODE"},"CFO":{"READ","WRITE","MESSAGE","ACCESS_FINANCE","SPEND_MONEY"},"Product Manager":{"READ","WRITE","CREATE_TASK","ASSIGN_TASK","MESSAGE"},"Developer":{"READ","WRITE","MESSAGE","RUN_CODE"},"QA Engineer":{"READ","WRITE","MESSAGE","RUN_CODE"}}
ACTION_PERMISSION={"SEND_MESSAGE":"MESSAGE","CREATE_TASK":"CREATE_TASK","SPEND_BUDGET":"SPEND_MONEY","DEPLOY":"DEPLOY","RUN_TEST":"RUN_CODE","HIRE_AGENT":"HIRE","FIRE_AGENT":"FIRE"}
HIGH_RISK={"SPEND_BUDGET","DEPLOY","FIRE_AGENT","HIRE_AGENT","DELETE_RESOURCE","MODIFY_PRODUCTION"}
class PermissionDenied(Exception):pass
class InvalidTransition(Exception):pass
class PermissionEngine:
    def check(self,agent:Agent,action_type:str)->None:
        needed=ACTION_PERMISSION.get(action_type,"WRITE")
        if needed not in ROLE_PERMISSIONS.get(agent.position,{"READ"}):raise PermissionDenied(f"{agent.position} lacks {needed}")
    def approval_required(self,autonomy:Autonomy,action_type:str,payload:dict)->bool:
        if autonomy==Autonomy.MANUAL:return True
        if autonomy==Autonomy.AUTONOMOUS:return False
        return action_type in HIGH_RISK or float(payload.get("amount",0))>=1000
class ActionEngine:
    def __init__(self,permissions=None):self.permissions=permissions or PermissionEngine()
    def submit(self,db:Session,company,agent:Agent,action_type:str,payload:dict,idempotency_key=None)->Action:
        if idempotency_key:
            old=db.scalar(select(Action).where(Action.idempotency_key==idempotency_key))
            if old:return old
        if agent.company_id!=company.id:raise PermissionDenied("Cross-company action denied")
        self.permissions.check(agent,action_type);approval=self.permissions.approval_required(company.autonomy,action_type,payload)
        a=Action(company_id=company.id,agent_id=agent.id,type=action_type,payload=payload,idempotency_key=idempotency_key,risk_level="HIGH" if action_type in HIGH_RISK else "LOW",requires_approval=approval,status="AWAITING_APPROVAL" if approval else "APPROVED")
        db.add(a);db.flush();self._audit(db,a,"ACTION_PROPOSED");return a
    def approve(self,db:Session,action:Action,approver:Agent)->Action:
        if action.status!="AWAITING_APPROVAL":raise InvalidTransition("action is not awaiting approval")
        if approver.company_id!=action.company_id:raise PermissionDenied("cross-company approval")
        action.status="APPROVED";action.approved_by=approver.id;action.approved_at=now();self._audit(db,action,"ACTION_APPROVED");return action
    def reject(self,db:Session,action:Action,approver:Agent,reason:str)->Action:
        if action.status!="AWAITING_APPROVAL":raise InvalidTransition("action is not awaiting approval")
        action.status="CANCELLED";action.failure_reason=reason;action.finished_at=now();self._audit(db,action,"ACTION_REJECTED");return action
    def queue(self,db:Session,action:Action)->Action:
        if action.status!="APPROVED":raise InvalidTransition("only approved actions can be queued")
        action.status="QUEUED";action.queued_at=now();self._audit(db,action,"ACTION_QUEUED");return action
    def execute(self,db:Session,action:Action)->Action:
        if action.status=="SUCCEEDED":return action
        if action.status!="QUEUED":raise InvalidTransition("only queued actions can execute")
        action.status="EXECUTING";action.started_at=now();attempt=ActionAttempt(action_id=action.id,attempt=action.retry_count+1,status="EXECUTING");db.add(attempt);db.flush()
        try:
            if action.type=="CREATE_TASK":
                p=action.payload;db.add(Task(company_id=action.company_id,title=p["title"],description=p.get("description",""),creator_id=action.agent_id,assignee_id=p.get("assignee_id",action.agent_id),priority=Priority(p.get("priority","MEDIUM")),status=TaskStatus.TODO));action.result={"created":"task"}
            elif action.type=="SPEND_BUDGET":
                from .finance import FinanceEngine
                company=__import__("app.models",fromlist=["Company"]).Company;co=db.get(company,action.company_id);FinanceEngine().record(db,co,"DEBIT",float(action.payload["amount"]),action.payload.get("category","OPERATIONS"),action.payload.get("description","Action spend"),reference_type="ACTION",reference_id=action.id);action.result={"spent":action.payload["amount"]}
            else: action.result={"executed":True}
            action.status="SUCCEEDED";action.finished_at=now();attempt.status="SUCCEEDED";attempt.finished_at=now();self._audit(db,action,"ACTION_SUCCEEDED");return action
        except Exception as exc:
            action.retry_count+=1;action.failure_reason=str(exc);action.status="FAILED" if action.retry_count>=action.max_retries else "APPROVED";attempt.status="FAILED";attempt.error=str(exc);attempt.finished_at=now();self._audit(db,action,"ACTION_FAILED");raise
    def cancel(self,db:Session,action:Action,reason="cancelled")->Action:
        if action.status in {"SUCCEEDED","FAILED","CANCELLED"}:raise InvalidTransition("terminal action")
        action.status="CANCELLED";action.failure_reason=reason;action.finished_at=now();self._audit(db,action,"ACTION_CANCELLED");return action
    def _audit(self,db,a,label):db.add(Activity(company_id=a.company_id,agent_id=a.agent_id,action=label,module="action_engine",status=a.status,detail=f"{a.type}:{a.id}"))
