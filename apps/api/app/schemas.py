from uuid import UUID
from pydantic import BaseModel,Field,ConfigDict
class CompanyCreate(BaseModel):
    name:str=Field(min_length=1,max_length=160)
    industry:str
    capital:float=Field(ge=0)
    goal:str=Field(min_length=1)
    horizon_days:int=Field(gt=0,le=3650)
    autonomy:str="SEMI_AUTONOMOUS"
    risk_tolerance:str="MEDIUM"
class CompanyOut(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id:UUID; name:str; industry:str; capital:float; cash:float; goal:str; horizon_days:int; autonomy:str; risk_tolerance:str; status:str; speed:int; tick_number:int
class TickOut(BaseModel):
    tick:int; activities:int; tasks_created:int; messages_created:int; decisions_created:int
