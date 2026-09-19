from dataclasses import dataclass
from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import KPI,KPIObservation
@dataclass
class KPITrend:
    current:float;previous:float|None;delta:float;percentage_change:float|None;moving_average:float;trend:str;observation_count:int
class KPITrendEngine:
    def calculate(self,db:Session,kpi:KPI,window:int=5)->KPITrend:
        rows=list(db.scalars(select(KPIObservation).where(KPIObservation.kpi_id==kpi.id).order_by(KPIObservation.created_at.desc()).limit(window)))
        vals=[x.value for x in reversed(rows)];current=vals[-1] if vals else kpi.value;previous=vals[-2] if len(vals)>1 else None;delta=current-previous if previous is not None else 0;pct=(delta/abs(previous)*100) if previous not in (None,0) else None
        if len(vals)<3:trend="INSUFFICIENT_DATA"
        else:
            diffs=[b-a for a,b in zip(vals,vals[1:])];spread=max(vals)-min(vals);avg=sum(vals)/len(vals)
            if spread>max(abs(avg)*.25,10) and any(x>0 for x in diffs) and any(x<0 for x in diffs):trend="VOLATILE"
            elif sum(diffs)/len(diffs)>max(abs(avg)*.01,.01):trend="RISING"
            elif sum(diffs)/len(diffs)<-max(abs(avg)*.01,.01):trend="FALLING"
            else:trend="STABLE"
        return KPITrend(current,previous,delta,pct,sum(vals)/len(vals) if vals else current,trend,len(vals))
    def company(self,db:Session,company_id)->dict:
        return {k.name:self.calculate(db,k).__dict__ for k in db.scalars(select(KPI).where(KPI.company_id==company_id))}
