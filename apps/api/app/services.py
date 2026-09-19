from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import Company,Agent,Task,Channel,Message,Decision,Activity,CompanyStatus,TaskStatus,Priority
from .finance import FinanceEngine
from .memory import MemoryService
CORE=[("Ada","CEO","Management",5),("Linus","CTO","Engineering",4),("Grace","Product Manager","Product",3),("Margaret","Developer","Engineering",2),("Edsger","QA Engineer","Engineering",2)]
CHANNELS=["general","management","engineering","marketing","sales","finance","support"]
def bootstrap_company(db:Session,company:Company):
    ceo=None
    for name,pos,dept,level in CORE:
        a=Agent(company_id=company.id,name=name,position=pos,department=dept,role_description=f"Own {pos} responsibilities",skills=[dept.lower()],goals=[company.goal],kpis={},permission_level=level,manager_id=ceo.id if ceo else None)
        db.add(a); db.flush()
        if pos=="CEO": ceo=a
    for name in CHANNELS: db.add(Channel(company_id=company.id,name=name))
    FinanceEngine().open_account(db,company)
    MemoryService().remember(db,company.id,None,"COMPANY",f"Goal: {company.goal}",1.0,{"kind":"goal"})
    db.add(Activity(company_id=company.id,agent_id=ceo.id,action="COMPANY_BOOTSTRAPPED",module="company",detail="Spawned five core agents"))
def run_tick(db:Session,company:Company):
    if company.status==CompanyStatus.PAUSED: raise ValueError("Company is paused")
    agents=db.scalars(select(Agent).where(Agent.company_id==company.id).order_by(Agent.permission_level.desc())).all()
    channels={c.name:c for c in db.scalars(select(Channel).where(Channel.company_id==company.id)).all()}
    by_role={a.position:a for a in agents}
    ceo,cto,pm,dev,qa=(by_role[x] for x in ("CEO","CTO","Product Manager","Developer","QA Engineer"))
    tasks=messages=decisions=0
    if company.tick_number==0:
        db.add(Decision(company_id=company.id,title="Initial execution strategy",problem="Turn company goal into executable work",context={"goal":company.goal},options=["vertical slice","broad parallel build"],participants=[str(ceo.id),str(cto.id),str(pm.id)],arguments={"vertical slice":"reduces integration risk","broad parallel build":"more surface area"},risk="MEDIUM",expected_outcome="Working measurable MVP path",final_decision="Build a working vertical slice first",decided_by=ceo.id))
        for assignee,title in [(pm,"Define MVP acceptance criteria"),(dev,"Implement first product increment"),(qa,"Create verification plan")]:
            db.add(Task(company_id=company.id,title=title,description=company.goal,creator_id=cto.id,assignee_id=assignee.id,priority=Priority.HIGH,status=TaskStatus.TODO)); tasks+=1
        db.add(Message(company_id=company.id,channel_id=channels["general"].id,sender_id=ceo.id,content=f"Company started. Goal: {company.goal}")); messages=1; decisions=1
    else:
        task=db.scalar(select(Task).where(Task.company_id==company.id,Task.status==TaskStatus.TODO).order_by(Task.created_at))
        if task:
            task.status=TaskStatus.IN_PROGRESS
            db.add(Message(company_id=company.id,channel_id=channels["engineering"].id,sender_id=task.assignee_id,content=f"Started task: {task.title}")); messages=1
    company.tick_number+=1
    db.add(Activity(company_id=company.id,agent_id=ceo.id,action="COMPANY_TICK",module="orchestrator",detail=f"tick={company.tick_number}; tasks={tasks}; messages={messages}; decisions={decisions}"))
    return company.tick_number,tasks,messages,decisions
