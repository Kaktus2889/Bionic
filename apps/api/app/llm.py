import asyncio,json,urllib.request
from abc import ABC,abstractmethod
from dataclasses import dataclass
from .config import settings
@dataclass(frozen=True)
class LLMResult:
    text:str; prompt_tokens:int=0; completion_tokens:int=0; cost:float=0; latency_ms:int=0
class LLMProvider(ABC):
    @abstractmethod
    async def complete(self,prompt:str,*,model:str)->LLMResult: ...
class DeterministicLLMProvider(LLMProvider):
    async def complete(self,prompt:str,*,model:str)->LLMResult:
        payload={"objective":"Advance the company goal using current signals","steps":[{"title":"Analyze highest-priority signal","owner_role":"Product Manager","priority":"HIGH"},{"title":"Implement bounded improvement","owner_role":"Developer","priority":"HIGH"},{"title":"Verify outcome and KPI impact","owner_role":"QA Engineer","priority":"MEDIUM"}],"expected_outcome":"Measurable progress toward the active goal"}
        return LLMResult(json.dumps(payload),prompt_tokens=len(prompt.split()),completion_tokens=45)
class CompatibleHTTPProvider(LLMProvider):
    def __init__(self,endpoint:str,api_key:str):self.endpoint=endpoint;self.api_key=api_key
    async def complete(self,prompt:str,*,model:str)->LLMResult:
        def call():
            body=json.dumps({"model":model,"messages":[{"role":"user","content":prompt}],"response_format":{"type":"json_object"}}).encode()
            req=urllib.request.Request(self.endpoint,data=body,headers={"Content-Type":"application/json","Authorization":f"Bearer {self.api_key}"})
            with urllib.request.urlopen(req,timeout=30) as r:data=json.loads(r.read())
            usage=data.get("usage",{});return LLMResult(data["choices"][0]["message"]["content"],usage.get("prompt_tokens",0),usage.get("completion_tokens",0))
        return await asyncio.to_thread(call)
class LLMRouter:
    def __init__(self,providers:dict[str,LLMProvider]): self.providers=providers
    async def route(self,kind:str,prompt:str)->LLMResult:
        models={"ROUTINE":settings.llm_routine_model,"ANALYSIS":settings.llm_analysis_model,"PLANNING":settings.llm_planning_model,"STRATEGIC":settings.llm_strategic_model,"STRATEGY":settings.llm_strategic_model,"EXECUTIVE_DECISION":settings.llm_strategic_model,"CODING":settings.llm_coding_model,"REFLECTION":settings.llm_reflection_model}
        model=models.get(kind,settings.llm_cheap_model);key="strong" if model in {settings.llm_planning_model,settings.llm_strategic_model,settings.llm_coding_model} else "cheap"
        if key not in self.providers: raise RuntimeError(f"No LLM provider configured for {key}")
        return await self.providers[key].complete(prompt,model=model)
def default_router()->LLMRouter:
    provider=CompatibleHTTPProvider(settings.llm_endpoint,settings.llm_api_key) if settings.llm_provider=="http" and settings.llm_endpoint and settings.llm_api_key else DeterministicLLMProvider()
    return LLMRouter({"strong":provider,"cheap":provider})
