from sqlalchemy import select,func
from sqlalchemy.orm import Session
from .models import Task,TaskStatus,Agent,Activity,ActionResult,AgentDecisionTrace,InformationRequest,now
from .memory import MemoryService
from .agent_decision import ObservationBuilder,ActionIntent,AgentReflection,ActionEvaluator,ActionPolicy
from .actions import ActionEngine,PermissionDenied
from .config import settings
class AgentRuntime:
    def candidates(self,obs:dict)->list[ActionIntent]:
        if obs["information_requests"]:
            q=obs["information_requests"][0];return [ActionIntent(type="SEND_MESSAGE",objective=q["objective"],reasoning_summary="A teammate is blocked and requested evidence.",expected_result="Requester receives useful information",confidence=.85,priority="HIGH",target=q["id"]),ActionIntent(type="WAIT",objective=q["objective"],reasoning_summary="Wait for more evidence.",expected_result="No change",confidence=.4)]
        if not obs["tasks"]:return [ActionIntent(type="WAIT",objective="Remain available",reasoning_summary="No assigned executable work.",expected_result="No unnecessary side effect",confidence=.95)]
        t=obs["tasks"][0];objective=t["title"]
        if t["status"]=="TODO":return [ActionIntent(type="WORK_ON_TASK",objective=objective,reasoning_summary="Assigned work is ready and relevant.",expected_result="Task enters progress",confidence=.9,priority="HIGH",target=t["id"]),ActionIntent(type="REQUEST_INFORMATION",objective=objective,reasoning_summary="Could request clarification before work.",expected_result="More context",confidence=.55,target=t["id"])]
        failed=any(x["status"]=="FAILED" for x in obs["recent_results"])
        if failed:return [ActionIntent(type="REQUEST_INFORMATION",objective=objective,reasoning_summary="Recent failure makes blind retry unsafe.",expected_result="Evidence for alternative approach",confidence=.82,priority="HIGH",target=t["id"]),ActionIntent(type="ESCALATE",objective=objective,reasoning_summary="Escalation is safer after repeated failure.",expected_result="Manager assistance",confidence=.72,target=t["id"])]
        return [ActionIntent(type="UPDATE_TASK",objective=objective,reasoning_summary="Current task has progressed and can be completed.",expected_result="Task completed and KPI can reflect result",confidence=.88,priority="HIGH",target=t["id"]),ActionIntent(type="REQUEST_REVIEW",objective=objective,reasoning_summary="Peer review is an alternative before completion.",expected_result="Independent verification",confidence=.62,target=t["id"])]
    def step(self,db:Session,company)->dict:
        task=db.scalar(select(Task).where(Task.company_id==company.id,Task.status.in_([TaskStatus.IN_PROGRESS,TaskStatus.TODO])).order_by(Task.created_at))
        if not task:return {"acted":False}
        agent=db.get(Agent,task.assignee_id);obs=ObservationBuilder().build(db,company,agent);cands=self.candidates(obs);selected=ActionEvaluator().choose(cands,obs);policy=ActionPolicy().check(db,company,agent,selected)
        trace=AgentDecisionTrace(company_id=company.id,agent_id=agent.id,objective=selected.objective,observation=obs,candidates=[x.model_dump() for x in cands],selected_intent=selected.model_dump(),policy_checks=policy);db.add(trace);db.flush()
        if not policy["allowed"]:
            db.add(Activity(company_id=company.id,agent_id=agent.id,action="INTENT_BLOCKED",module="agent_runtime_v2",detail=f"{selected.type}: policy denied"));return {"acted":False,"intent":selected.type}
        result=self._execute(db,company,agent,selected,task);trace.result=result
        if result["status"] in {"SUCCEEDED","FAILED"}:
            ref=AgentReflection(outcome=result["output_summary"],success=result["status"]=="SUCCEEDED",lesson="Successful bounded action can advance this objective." if result["status"]=="SUCCEEDED" else "Do not repeat the same failed action without new evidence.",unexpected_result=result.get("error"),memory_candidate=result["output_summary"] if result["status"]=="SUCCEEDED" else f"Failure on {selected.objective}: {result.get('error')}",strategy_signal=None,follow_up_needed=result["status"]!="SUCCEEDED");trace.reflection=ref.model_dump()
            if ref.memory_candidate:MemoryService().remember_if_worthy(db,company.id,agent.id,"EPISODIC",ref.memory_candidate,.72 if ref.success else .8,source="REFLECTION",task_id=task.id)
        db.add(Activity(company_id=company.id,agent_id=agent.id,action="AGENT_INTENT_SELECTED",module="agent_runtime_v2",detail=f"{selected.type}: {selected.reasoning_summary}"));return {"acted":True,"intent":selected.type,"result":result}
    def _execute(self,db,company,agent,intent,task):
        start=now();status="SUCCEEDED";error=None;summary=""
        try:
            if intent.type=="WORK_ON_TASK":task.status=TaskStatus.IN_PROGRESS;summary=f"WORK_ON_TASK started {task.title}"
            elif intent.type=="UPDATE_TASK":task.status=TaskStatus.DONE;task.completed_at=now();task.actual_effort=1;summary=f"UPDATE_TASK completed {task.title}"
            elif intent.type=="REQUEST_INFORMATION":
                recipient=db.get(Agent,agent.manager_id) if agent.manager_id else db.scalar(select(Agent).where(Agent.company_id==company.id,Agent.position=="Product Manager"))
                db.add(InformationRequest(company_id=company.id,requester_id=agent.id,recipient_id=recipient.id,objective=intent.objective,question=f"Provide evidence needed to continue: {intent.objective}"));task.status=TaskStatus.BLOCKED;task.blocked_reason="NEED_INFORMATION";summary="REQUEST_INFORMATION created"
            elif intent.type=="SEND_MESSAGE":
                req=db.get(InformationRequest,intent.target);req.response=f"{agent.position} response: proceed using current validated task context.";req.status="RESOLVED";req.resolved_at=now();blocked=db.scalar(select(Task).where(Task.company_id==company.id,Task.status==TaskStatus.BLOCKED,Task.blocked_reason=="NEED_INFORMATION").order_by(Task.created_at)); 
                if blocked:blocked.status=TaskStatus.IN_PROGRESS;blocked.blocked_reason=None
                summary="SEND_MESSAGE resolved information request"
            elif intent.type=="WAIT":summary="WAIT no side effect"
            else:
                action=ActionEngine().submit(db,company,agent,intent.type,intent.parameters,idempotency_key=f"intent:{agent.id}:{intent.objective}:{intent.type}")
                trace_action=action.id
                if action.status=="APPROVED":ActionEngine().queue(db,action);ActionEngine().execute(db,action)
                summary=f"{intent.type} submitted through ActionEngine"
        except Exception as exc:status="FAILED";error=str(exc);summary=f"{intent.type} failed"
        duration=int((now()-start).total_seconds()*1000);r=ActionResult(action_id=action.id if 'action' in locals() else __import__('uuid').uuid4(),company_id=company.id,agent_id=agent.id,status=status,output_summary=summary,error=error,duration_ms=duration,cost=intent.estimated_cost,affected_entities=[str(task.id)],observed_effects={"task_status":task.status.value});db.add(r);return {"status":status,"output_summary":summary,"error":error,"duration_ms":duration}
