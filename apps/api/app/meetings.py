from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import Meeting,MeetingParticipant,MeetingContribution,Agent,Decision,Task,Priority,TaskStatus,Activity
from .memory import MemoryService
class MeetingEngine:
    def create(self,db:Session,company,owner:Agent,participants:list[Agent],agenda:str,meeting_type="REVIEW",context=None)->Meeting:
        m=Meeting(company_id=company.id,owner_id=owner.id,agenda=agenda,type=meeting_type,context=context or {});db.add(m);db.flush()
        for a in participants:db.add(MeetingParticipant(meeting_id=m.id,agent_id=a.id,role="OWNER" if a.id==owner.id else "PARTICIPANT"))
        return m
    def execute(self,db:Session,meeting:Meeting)->Decision:
        if meeting.status=="COMPLETED": return db.scalar(select(Decision).where(Decision.company_id==meeting.company_id,Decision.context["meeting_id"].as_string()==str(meeting.id)))
        meeting.status="IN_PROGRESS";parts=list(db.scalars(select(MeetingParticipant).where(MeetingParticipant.meeting_id==meeting.id)))
        views=[]
        for p in parts:
            a=db.get(Agent,p.agent_id); memories=MemoryService().retrieve(db,meeting.company_id,a.id,query=meeting.agenda,limit=4)
            view=f"{a.position}: prioritize {meeting.agenda}; context={'; '.join(x.content for x in memories[:2])}";views.append(view);db.add(MeetingContribution(meeting_id=meeting.id,agent_id=a.id,content=view))
        meeting.summary=" | ".join(views)
        d=Decision(company_id=meeting.company_id,title=f"Meeting: {meeting.agenda}",problem=meeting.agenda,context={"meeting_id":str(meeting.id)},options=["act","defer"],participants=[str(p.agent_id) for p in parts],arguments={"views":meeting.summary},risk="MEDIUM",expected_outcome="Resolve meeting agenda",final_decision="Act on agreed priority",decided_by=meeting.owner_id);db.add(d);db.flush()
        db.add(Task(company_id=meeting.company_id,title=f"Action item: {meeting.agenda}",description=meeting.summary,creator_id=meeting.owner_id,assignee_id=meeting.owner_id,priority=Priority.HIGH,status=TaskStatus.TODO))
        meeting.status="COMPLETED";MemoryService().remember_if_worthy(db,meeting.company_id,meeting.owner_id,"DECISION",meeting.summary,.85,source="MEETING",decision_id=d.id,meeting_id=meeting.id)
        db.add(Activity(company_id=meeting.company_id,agent_id=meeting.owner_id,action="MEETING_COMPLETED",module="meeting_engine",detail=meeting.agenda));return d
