import asyncio
from redis.asyncio import Redis
from app.config import settings
from app.db import SessionLocal
from app.models import Company,CompanyStatus
from app.services import run_tick
async def run():
    redis=Redis.from_url(settings.redis_url,decode_responses=True)
    while True:
        item=await redis.blpop("company:ticks",timeout=5)
        if not item: continue
        _,company_id=item
        with SessionLocal() as db:
            company=db.get(Company,company_id)
            if company and company.status!=CompanyStatus.PAUSED:
                try: run_tick(db,company); db.commit()
                except Exception:
                    db.rollback(); raise
if __name__=="__main__": asyncio.run(run())
