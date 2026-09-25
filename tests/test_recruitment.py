import io,json
import pytest
from fastapi.testclient import TestClient
from docx import Document
from backend.main import app
from backend import recruitment,local_model
from backend.store import connect

@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setenv('MIZAN_DB',str(tmp_path/'hiring.sqlite3'))
    with TestClient(app,headers={'X-Mizan-Action':'1'}) as c:
        c.post('/api/login',json={'username':'admin','password':'Mizan-demo-2026!'})
        yield c

def create_job(c):
    rid=c.post('/api/scenarios/shortfall/requisitions',json={'demand_id':'D001'}).json()['id']
    criteria=[{'id':'skill','category':'technical_skill','description':'Machine learning experience','weight':70},{'id':'teaching','category':'teaching','description':'University teaching','weight':30}]
    r=c.post(f'/api/recruitment/requisitions/{rid}/approve',json={'title':'Lecturer','criteria':criteria})
    assert r.status_code==200,r.text
    return r.json()['id'],criteria

def test_source_checks_staleness_and_html_escape(client,monkeypatch):
    jid,criteria=create_job(client)
    text='Machine learning research and Python. <script>alert(1)</script>'
    cid=client.post(f'/api/recruitment/jobs/{jid}/candidates',json={'name':'Test Candidate','text':text}).json()['id']
    monkeypatch.setattr(local_model,'status',lambda:{'available':True})
    monkeypatch.setattr(local_model,'structured',lambda *a,**k:({'findings':[{'criterion_id':'skill','status':'supported','quote':'Machine learning research'},{'criterion_id':'teaching','status':'supported','quote':'University teaching for ten years'}]},{}))
    r=client.post(f'/api/recruitment/candidates/{cid}/assess',json={})
    assert r.status_code==200,r.text
    assert r.json()['evidence_score']==70
    assert r.json()['findings'][1]['status']=='unknown'
    brief=client.get(f'/api/recruitment/candidates/{cid}/brief').text
    assert '<script>' not in brief and '&lt;script&gt;' in brief
    assert client.put(f'/api/recruitment/jobs/{jid}',json={'title':'Lecturer','criteria':criteria,'revision':1}).status_code==200
    assert client.get(f'/api/recruitment/jobs/{jid}/candidates').json()[0]['assessment'] is None
    assert client.put(f'/api/recruitment/jobs/{jid}',json={'title':'Lecturer','criteria':criteria,'revision':1}).status_code==409

def test_hiring_role_cannot_access_student_records(client):
    jid,_=create_job(client)
    client.post('/api/login',json={'username':'hiring_manager','password':'Mizan-demo-2026!'})
    d=client.get('/api/scenarios/baseline').json()
    assert d['students']==[] and d['professors']==[] and d['sections']==[]
    assert client.get('/api/scenarios/baseline/export').status_code==403
    assert client.get('/api/recruitment/jobs').status_code==200
    assert client.get('/api/agents/runs?scenario_id=baseline').status_code==403
    client.post('/api/login',json={'username':'student','password':'Mizan-demo-2026!'})
    assert client.get(f'/api/recruitment/jobs/{jid}/candidates').status_code==403

def test_cv_upload_and_rejection(client):
    jid,_=create_job(client)
    doc=Document();doc.add_paragraph('Machine learning lecturer with university teaching experience.');stream=io.BytesIO();doc.save(stream)
    r=client.post(f'/api/recruitment/jobs/{jid}/upload',files={'file':('example.docx',stream.getvalue(),'application/octet-stream')})
    assert r.status_code==200,r.text
    assert client.get(f'/api/recruitment/jobs/{jid}/candidates').json()[0]['text'].startswith('Machine learning')
    assert client.post(f'/api/recruitment/jobs/{jid}/upload',files={'file':('bad.exe',b'bad','application/octet-stream')}).status_code==422
    assert client.post(f'/api/recruitment/jobs/{jid}/upload',files={'file':('big.txt',b'x'*(5*1024*1024+1),'text/plain')}).status_code==422

def test_stale_shortage_cannot_authorize(client):
    rid=client.post('/api/scenarios/shortfall/requisitions',json={'demand_id':'D001'}).json()['id']
    with connect() as con:con.execute("UPDATE scenarios SET revision=revision+1 WHERE id='shortfall'")
    r=client.post(f'/api/recruitment/requisitions/{rid}/approve',json={'title':'Lecturer','criteria':[{'id':'skill','category':'technical_skill','description':'Machine learning','weight':100}]})
    assert r.status_code==409

def test_local_model_rejects_external_server(monkeypatch):
    monkeypatch.setenv('MIZAN_MODEL_URL','https://example.com')
    with pytest.raises(ValueError):local_model.base_url()
