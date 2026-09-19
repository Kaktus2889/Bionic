from sqlalchemy import select,func
from sqlalchemy.orm import Session
from .models import KPI,KPIObservation,Task,TaskStatus,Customer,Event,Transaction
from .finance import FinanceEngine
class KPIEngine:
    TARGETS={"task_completion_rate":100,"revenue":0,"expenses":0,"cash":0,"burn_rate":0,"runway":365,"customer_count":1,"customer_satisfaction":100,"churn":0,"open_critical_events":0}
    def measure(self,db:Session,company)->dict[str,float]:
        total=db.scalar(select(func.count(Task.id)).where(Task.company_id==company.id)) or 0;done=db.scalar(select(func.count(Task.id)).where(Task.company_id==company.id,Task.status==TaskStatus.DONE)) or 0
        fin=FinanceEngine().summary(db,company.id);customers=db.scalar(select(func.count(Customer.id)).where(Customer.company_id==company.id)) or 0
        churn=db.scalar(select(func.count(Customer.id)).where(Customer.company_id==company.id,Customer.status=="CHURNED")) or 0
        critical=db.scalar(select(func.count(Event.id)).where(Event.company_id==company.id,Event.priority=="CRITICAL",Event.status!="PROCESSED")) or 0
        expense_30=float(db.scalar(select(func.coalesce(func.sum(Transaction.amount),0)).where(Transaction.company_id==company.id,Transaction.type=="DEBIT",Transaction.status=="POSTED")) or 0)
        satisfaction=float(db.scalar(select(func.avg(Customer.context["satisfaction"].as_float())).where(Customer.company_id==company.id,Customer.context.has_key("satisfaction"))) or 100) if customers else 100
        vals={"task_completion_rate":100*done/total if total else 0,"revenue":fin["revenue"],"expenses":fin["expenses"],"cash":fin["cash"],"burn_rate":expense_30,"runway":fin["cash"]/expense_30*30 if expense_30>0 else 3650,"customer_count":float(customers),"customer_satisfaction":satisfaction,"churn":100*churn/customers if customers else 0,"open_critical_events":float(critical)}
        for name,value in vals.items():
            k=db.scalar(select(KPI).where(KPI.company_id==company.id,KPI.name==name))
            if not k:k=KPI(company_id=company.id,name=name,value=value,target=self.TARGETS[name],unit="percent" if name in {"task_completion_rate","customer_satisfaction","churn"} else "count");db.add(k);db.flush()
            k.value=value;k.measured_at=__import__("app.models",fromlist=["now"]).now();db.add(KPIObservation(kpi_id=k.id,company_id=company.id,value=value,target=k.target,source="DOMAIN_STATE",metadata_={"tick":company.tick_number}))
        return vals
