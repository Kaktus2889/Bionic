import json
from pydantic import TypeAdapter,ValidationError
from .agent_decision import ActionIntent
from .llm import default_router
class IntentPlanner:
    async def propose(self,observation:dict,fallback:list[ActionIntent])->list[ActionIntent]:
        prompt="Return JSON array of 1-4 ActionIntent objects. Allowed tools: "+json.dumps(observation["tools"])+" Observation: "+json.dumps(observation,default=str)[:6000]
        router=default_router();adapter=TypeAdapter(list[ActionIntent])
        for _ in range(2):
            try:
                result=await router.route("ANALYSIS",prompt)
                if not result.text.strip():raise ValueError("empty response")
                intents=adapter.validate_json(result.text)
                if intents:return intents[:4]
            except (ValidationError,ValueError,json.JSONDecodeError,TimeoutError,RuntimeError):
                prompt+=" Invalid response. Return only valid JSON array matching the schema."
        return fallback[:4]
