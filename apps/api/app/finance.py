from sqlalchemy import select,func
from sqlalchemy.orm import Session
from .models import CompanyAccount,Transaction
class FinanceEngine:
    def open_account(self,db:Session,company)->CompanyAccount:
        a=CompanyAccount(company_id=company.id,balance=company.capital); db.add(a); db.flush(); db.add(Transaction(company_id=company.id,account_id=a.id,type="CREDIT",category="CAPITAL",amount=company.capital,description="Initial capital",simulated=False)); return a
    def record(self,db:Session,company,kind:str,amount:float,category:str,description:str,simulated:bool=False)->Transaction:
        if amount<=0: raise ValueError("amount must be positive")
        a=db.scalar(select(CompanyAccount).where(CompanyAccount.company_id==company.id))
        if not a: raise RuntimeError("company account missing")
        delta=amount if kind=="CREDIT" else -amount
        if a.balance+delta<0: raise ValueError("insufficient funds")
        a.balance+=delta; company.cash=a.balance
        t=Transaction(company_id=company.id,account_id=a.id,type=kind,category=category,amount=amount,description=description,simulated=simulated); db.add(t); return t
    def summary(self,db:Session,company_id)->dict:
        a=db.scalar(select(CompanyAccount).where(CompanyAccount.company_id==company_id))
        revenue=db.scalar(select(func.coalesce(func.sum(Transaction.amount),0)).where(Transaction.company_id==company_id,Transaction.type=="CREDIT",Transaction.category!="CAPITAL"))
        expenses=db.scalar(select(func.coalesce(func.sum(Transaction.amount),0)).where(Transaction.company_id==company_id,Transaction.type=="DEBIT"))
        return {"cash":a.balance if a else 0,"revenue":float(revenue or 0),"expenses":float(expenses or 0),"profit":float(revenue or 0)-float(expenses or 0)}
