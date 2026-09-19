import asyncio
from redis.asyncio import Redis
from sqlalchemy import select
from app.config import settings
from app.db import SessionLocal
from app.models import Action,Company,CompanyStatus
from app.actions import ActionEngine
from app.runtime import CompanyRuntime
async def action_worker(redis):
    while True:
        item=await redis.blpop("actions:execute",timeout=2)
        if not item:continue
        _,action_id=item
        with SessionLocal() as db:
            action=db.get(Action,action_id)
            if not action or action.status=="SUCCEEDED":continue
            try:ActionEngine().execute(db,action);db.commit()
            except Exception:
                db.rollback()
                with SessionLocal() as retry_db:
                    retry=retry_db.get(Action,action_id)
                    if retry and retry.status=="APPROVED":retry.status="QUEUED";retry_db.commit();await redis.rpush("actions:execute",action_id)
async def scheduler(redis):
    while True:
        with SessionLocal() as db: ids=[str(x) for x in db.scalars(select(Company.id).where(Company.status==CompanyStatus.RUNNING))]
        for company_id in ids:
            lock=redis.lock(f"company-cycle:{company_id}",timeout=settings.cycle_lock_ttl,blocking_timeout=0)
            if not await lock.acquire():continue
            try:
                with SessionLocal() as db:
                    company=db.get(Company,company_id)
                    if company and company.status==CompanyStatus.RUNNING:
                        cycles={1:1,5:2,20:3,100:4}.get(company.speed,1)
                        for _ in range(cycles):
                            if company.status!=CompanyStatus.RUNNING:break
                            try:await CompanyRuntime().cycle(db,company);db.commit()
                            except Exception:db.commit();break
            finally:
                try:await lock.release()
                except Exception:pass
        await asyncio.sleep(1)
async def run():
    redis=Redis.from_url(settings.redis_url,decode_responses=True)
    await asyncio.gather(action_worker(redis),scheduler(redis))
if __name__=="__main__":asyncio.run(run())
