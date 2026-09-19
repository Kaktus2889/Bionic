from abc import ABC,abstractmethod
from dataclasses import dataclass
@dataclass(frozen=True)
class LLMResult:
    text:str; prompt_tokens:int=0; completion_tokens:int=0; cost:float=0; latency_ms:int=0
class LLMProvider(ABC):
    @abstractmethod
    async def complete(self,prompt:str,*,model:str)->LLMResult: ...
class LLMRouter:
    def __init__(self,providers:dict[str,LLMProvider]): self.providers=providers
    async def route(self,kind:str,prompt:str)->LLMResult:
        key="strong" if kind in {"STRATEGY","CODING","EXECUTIVE_DECISION"} else "cheap"
        if key not in self.providers: raise RuntimeError(f"No LLM provider configured for {key}")
        return await self.providers[key].complete(prompt,model=key)
