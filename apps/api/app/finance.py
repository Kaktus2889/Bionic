from sqlalchemy import select,func
from sqlalchemy.orm import Session
from .models import CompanyAccount,Transaction,Budget
class FinanceEngine:
    def open_account(self,db:Session,company)->CompanyAccount:
        a=CompanyAccount(company_id=company.id,balance=0);db.add(a);db.flush();db.add(Transaction(company_id=company.id,account_id=a.id,type="CREDIT",category="CAPITAL",amount=company.capital,description="Initial capital",simulated=False,status="POSTED"));db.flush();return a
    def balance(self,db:Session,company_id)->float:
        credits=db.scalar(select(func.coalesce(func.sum(Transaction.amount),0)).where(Transaction.company_id==company_id,Transaction.type=="CREDIT",Transaction.status=="POSTED")) or 0
        debits=db.scalar(select(func.coalesce(func.sum(Transaction.amount),0)).where(Transaction.company_id==company_id,Transaction.type=="DEBIT",Transaction.status=="POSTED")) or 0
        return float(credits)-float(debits)
    def record(self,db:Session,company,kind:str,amount:float,category:str,description:str,simulated:bool=False,status="POSTED",reference_type=None,reference_id=None)->Transaction:
        if kind not in {"CREDIT","DEBIT"} or amount<=0:raise ValueError("invalid transaction")
        if kind=="DEBIT" and status=="POSTED" and self.balance(db,company.id)<amount:raise ValueError("insufficient funds")
        a=db.scalar(select(CompanyAccount).where(CompanyAccount.company_id==company.id))
        if not a:raise RuntimeError("company account missing")
        t=Transaction(company_id=company.id,account_id=a.id,type=kind,category=category,amount=amount,description=description,simulated=simulated,status=status,reference_type=reference_type,reference_id=reference_id);db.add(t);return t
    def transfer(self,db:Session,company,amount:float,description:str)->tuple[Transaction,Transaction]:
        return (self.record(db,company,"DEBIT",amount,"TRANSFER",description),self.record(db,company,"CREDIT",amount,"TRANSFER",description))
    def summary(self,db:Session,company_id)->dict:
        revenue=db.scalar(select(func.coalesce(func.sum(Transaction.amount),0)).where(Transaction.company_id==company_id,Transaction.type=="CREDIT",Transaction.category!="CAPITAL",Transaction.category!="TRANSFER",Transaction.status=="POSTED")) or 0
        expenses=db.scalar(select(func.coalesce(func.sum(Transaction.amount),0)).where(Transaction.company_id==company_id,Transaction.type=="DEBIT",Transaction.category!="TRANSFER",Transaction.status=="POSTED")) or 0
        return {"cash":self.balance(db,company_id),"revenue":float(revenue),"expenses":float(expenses),"profit":float(revenue)-float(expenses)}
