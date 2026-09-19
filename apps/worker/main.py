import asyncio
from redis.asyncio import Redis
from app.config import settings
from app.db import SessionLocal
from app.models import Action
from app.actions import ActionEngine
async def run():
    redis=Redis.from_url(settings.redis_url,decode_responses=True)
    while True:
        item=await redis.blpop("actions:execute",timeout=5)
        if not item:continue
        _,action_id=item
        with SessionLocal() as db:
            action=db.get(Action,action_id)
            if not action:continue
            try:ActionEngine().execute(db,action);db.commit()
            except Exception:
                db.rollback()
                with SessionLocal() as retry_db:
                    retry=retry_db.get(Action,action_id)
                    if retry and retry.status=="APPROVED":
                        retry.status="QUEUED";retry_db.commit();await redis.rpush("actions:execute",action_id)
if __name__=="__main__":asyncio.run(run())
