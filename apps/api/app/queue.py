from redis import Redis
from .config import settings
class ActionQueue:
    key="actions:execute"
    def __init__(self,client=None):self.client=client or Redis.from_url(settings.redis_url,decode_responses=True)
    def enqueue(self,action_id):self.client.rpush(self.key,str(action_id))
    def pop(self,timeout=1):
        item=self.client.blpop(self.key,timeout=timeout);return item[1] if item else None
