import os
os.environ["DATABASE_URL"]="sqlite+pysqlite:///./test_api.db"
from fastapi.testclient import TestClient
from app.db import Base,engine
from app.main import app
Base.metadata.create_all(engine)
client=TestClient(app)
def test_vertical_slice():
    p={"name":"Acme AI","industry":"SaaS","capital":50000,"goal":"Get first 100 paying customers","horizon_days":90,"autonomy":"SEMI_AUTONOMOUS","risk_tolerance":"MEDIUM"}
    r=client.post("/companies",json=p); assert r.status_code==201
    cid=r.json()["id"]; assert len(client.get(f"/companies/{cid}/agents").json())==5
    assert client.post(f"/companies/{cid}/tick").status_code==409
    assert client.post(f"/companies/{cid}/start").status_code==200
    t=client.post(f"/companies/{cid}/tick"); assert t.status_code==200 and t.json()["tasks_created"]==3
    assert len(client.get(f"/companies/{cid}/tasks").json())==3
    assert len(client.get(f"/companies/{cid}/messages").json())==1
    assert len(client.get(f"/companies/{cid}/decisions").json())==1
    assert client.post(f"/companies/{cid}/pause").json()["status"]=="PAUSED"
