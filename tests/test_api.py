import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.fixtures import generate
from backend.store import connect


@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setenv("MIZAN_DB",str(tmp_path/"test.sqlite3"))
    monkeypatch.delenv("MIZAN_DEMO_PASSWORD",raising=False)
    with TestClient(app,headers={"X-Mizan-Action":"1"}) as c:
        assert c.post('/api/login',json={"username":"admin","password":"Mizan-demo-2026!"}).status_code==200
        yield c


def good_change(client,start=540):
    r=client.post('/api/scenarios/baseline/changes',json={"section_id":"S001","meeting_index":0,"day":0,"start":start,"reason":"Test change request"})
    assert r.status_code==200,r.text
    assert r.json()["status"]=="recommended"
    return r.json()["id"]


def test_approval_publication_and_stale_rejection(client):
    a,b=good_change(client),good_change(client)
    assert client.post(f'/api/proposals/{a}/publish',json={}).status_code==409
    assert client.post(f'/api/proposals/{a}/approve',json={}).status_code==200
    assert client.post(f'/api/proposals/{b}/approve',json={}).status_code==200
    assert client.post(f'/api/proposals/{a}/publish',json={}).status_code==200
    assert client.post(f'/api/proposals/{b}/publish',json={}).status_code==409
    assert client.get('/api/scenarios/baseline').json()["revision"]==2
    with connect() as db:
        assert db.execute("SELECT count(*) FROM versions WHERE scenario_id='baseline'").fetchone()[0]==2
    assert client.post(f'/api/proposals/{a}/reject',json={}).status_code==409


def test_invalid_change_blocked_and_alternatives_validated(client):
    r=client.post('/api/scenarios/baseline/changes',json={"section_id":"S001","meeting_index":0,"day":0,"start":600,"reason":"Conflict example"}).json()
    assert r["status"]=="invalid"
    assert r["analysis"]["conflict_count"]>0
    assert r["analysis"]["alternatives"]
    assert client.post(f'/api/proposals/{r["id"]}/approve',json={}).status_code==409
    alternative=r["analysis"]["alternatives"][0]["section"]
    result=client.post('/api/scenarios/baseline/alternative',json={"section":alternative})
    assert result.status_code==200 and result.json()["status"]=="recommended"


def test_student_isolation_and_server_authorization(client):
    client.post('/api/login',json={"username":"student","password":"Mizan-demo-2026!"})
    d=client.get('/api/scenarios/baseline').json()
    assert len(d["students"])==1 and d["students"][0]["id"]=="ST0001"
    assert not d["professors"]
    for route in ['/api/scenarios/baseline/export','/api/scenarios/baseline/metrics','/api/audit','/api/requisitions','/api/scenarios/baseline/workforce','/api/proposals?scenario_id=baseline']:
        assert client.get(route).status_code==403
    assert client.post('/api/scenarios/baseline/optimize',json={}).status_code==403


def test_professor_cannot_move_others_sections(client):
    client.post('/api/login',json={"username":"professor","password":"Mizan-demo-2026!"})
    assert client.post('/api/scenarios/baseline/changes',json={"section_id":"S010","meeting_index":0,"day":0,"start":540,"reason":"Not my section"}).status_code==403
    data=client.get('/api/scenarios/baseline').json()
    assert data["students"]==[]
    assert all(s["professor_id"]=="P001" for s in data["sections"])


def test_import_export_roundtrip_and_invalid_references(client):
    raw=generate(groups=1,per_group=2).model_dump()
    imported=client.post('/api/import',json=raw)
    assert imported.status_code==200
    assert client.get(f'/api/scenarios/{imported.json()["id"]}/export').json()==raw
    raw["sections"][0]["room_id"]="nonexistent"
    assert client.post('/api/import',json=raw).status_code==422


def test_policy_invalidates_approval(client):
    pid=good_change(client)
    client.post(f'/api/proposals/{pid}/approve',json={})
    data=client.get('/api/scenarios/baseline').json()
    result=client.post('/api/scenarios/baseline/policy',json={"revision":data["revision"],"policy":data["policy"]})
    assert result.status_code==200
    assert client.post(f'/api/proposals/{pid}/publish',json={}).status_code==409


def test_requisition_requires_proven_shortage(client):
    assert client.post('/api/scenarios/baseline/requisitions',json={"demand_id":"D001"}).status_code==422
    result=client.post('/api/scenarios/shortfall/requisitions',json={"demand_id":"D001"})
    assert result.status_code==200
    assert client.get('/api/requisitions').json()[0]["data"]["minimum_unservable_sections"]==1


def test_csrf_guard_and_logout(client):
    assert client.post('/api/logout',json={},headers={"X-Mizan-Action":"0"}).status_code==403
    assert client.post('/api/logout',json={},headers={"Origin":"https://untrusted.example"}).status_code==403
    assert client.post('/api/logout',json={}).status_code==200
    assert client.get('/api/me').status_code==401
