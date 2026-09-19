import hashlib,json,math,urllib.request
from abc import ABC,abstractmethod
from .config import settings
class EmbeddingProvider(ABC):
    @abstractmethod
    def embed(self,text:str)->list[float]:...
class DeterministicEmbeddingProvider(EmbeddingProvider):
    dimensions=32
    def embed(self,text:str)->list[float]:
        raw=hashlib.sha256(text.lower().encode()).digest();v=[(raw[i]-127.5)/127.5 for i in range(self.dimensions)];norm=math.sqrt(sum(x*x for x in v)) or 1;return [x/norm for x in v]
class RealEmbeddingProvider(EmbeddingProvider):
    def __init__(self,endpoint,key,model):self.endpoint=endpoint;self.key=key;self.model=model
    def embed(self,text:str)->list[float]:
        req=urllib.request.Request(self.endpoint,data=json.dumps({"model":self.model,"input":text,"dimensions":32}).encode(),headers={"Content-Type":"application/json","Authorization":f"Bearer {self.key}"})
        with urllib.request.urlopen(req,timeout=20) as r:return list(json.loads(r.read())["data"][0]["embedding"])
def embedding_provider()->EmbeddingProvider:
    if settings.embedding_provider=="http" and settings.embedding_endpoint and settings.embedding_api_key:return RealEmbeddingProvider(settings.embedding_endpoint,settings.embedding_api_key,settings.embedding_model)
    return DeterministicEmbeddingProvider()
