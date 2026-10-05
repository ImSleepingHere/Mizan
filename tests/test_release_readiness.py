"""Regression checks for the defects reproduced during the independent October review."""
import json
import pytest
from fastapi.testclient import TestClient
from backend.main import app, redact, scenario
from backend.edugate_routes import build, ImportBody
from backend.fixtures import generate
from backend.models import Semester, Window
from backend.request_routes import preview


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv('MIZAN_DB', str(tmp_path / 'release.sqlite3'))
    monkeypatch.delenv('MIZAN_DEMO_PASSWORD', raising=False)
    with TestClient(app, headers={'X-Mizan-Action': '1'}) as c:
        assert c.post('/api/login', json={'username':'admin','password':'Mizan-demo-2026!'}).status_code == 200
        yield c


def imported(c):
    rows = [dict(code='FIN 202', section='1', days=[0], start=480, end=540, room='A-01'),
            dict(code='MKT 201', section='1', days=[0], start=480, end=540, room='A-02')]
    a=c.post('/api/edugate/import', json=dict(student_id='202612345', student_name='Fictional A', rows=[rows[0]])).json()
    assert 'id' in a
    b=c.post('/api/edugate/import', json=dict(student_id='OTHER-9', student_name='Fictional B', scenario_id=a['id'], rows=[rows[1]]))
    assert b.status_code==200
    return a['id']


@pytest.mark.parametrize('explicit', [False, True])
def test_shared_instructor_is_linked_and_overlap_blocks_readiness(client, explicit):
    sid=imported(client)
    facts=[dict(section_id=s, name='Dr Same Person', **({'instructor_id':'P-REAL'} if explicit else {})) for s in ['FIN202-1','MKT201-1']]
    r=client.post(f'/api/edugate/{sid}/verify',json=dict(rooms=[dict(id='A-01',capacity=20),dict(id='A-02',capacity=20)],instructors=facts))
    assert r.status_code==200,r.text
    assert r.json()['facts_verified'] and not r.json()['ready_to_publish']
    assert any(i['code']=='PROFESSOR_OVERLAP' for i in r.json()['issues'])
    data=client.get(f'/api/scenarios/{sid}').json()
    assert len({s['professor_id'] for s in data['sections']})==1
    assert len(data['professors'])==1


def test_same_name_distinct_explicit_ids_and_small_room(client):
    sid=imported(client)
    r=client.post(f'/api/edugate/{sid}/verify',json=dict(rooms=[dict(id='A-01',capacity=20),dict(id='A-02',capacity=20)],
        instructors=[dict(section_id='FIN202-1',name='Same Name',instructor_id='P1'),dict(section_id='MKT201-1',name='Same Name',instructor_id='P2')]))
    assert r.status_code==200 and r.json()['ready_to_publish']
    assert all(s['capacity']==20 for s in client.get(f'/api/scenarios/{sid}').json()['sections'])


def test_verified_section_capacity_is_not_silently_lowered(client):
    sid=imported(client)
    client.post(f'/api/edugate/{sid}/verify',json=dict(sections=[dict(id='FIN202-1',capacity=30)]))
    r=client.post(f'/api/edugate/{sid}/verify',json=dict(rooms=[dict(id='A-01',capacity=20)]))
    assert any(i['code']=='CAPACITY' for i in r.json()['issues'])


def test_whitespace_name_and_reused_id_different_name_rejected(client):
    sid=imported(client)
    assert client.post(f'/api/edugate/{sid}/verify',json=dict(instructors=[dict(section_id='FIN202-1',name='  ')])).status_code==422
    assert client.post(f'/api/edugate/{sid}/verify',json=dict(instructors=[dict(section_id='FIN202-1',name='One Person',instructor_id='P1')])).status_code==200
    assert client.post(f'/api/edugate/{sid}/verify',json=dict(instructors=[dict(section_id='MKT201-1',name='Other Person',instructor_id='P1')])).status_code==422


def test_subsequent_import_preserves_resource_availability(client):
    sid=imported(client)
    _,base=scenario(sid)
    limited=[Window(day=0,start=480,end=600)]
    base.rooms[0].availability=limited
    base.professors[0].availability=limited
    body=ImportBody(student_id='NEXT',student_name='Next',rows=[dict(code='FIN 202',section='1',days=[0],start=480,end=540,room='A-01')])
    result,_=build(body,base)
    assert result.rooms[0].availability==limited and result.professors[0].availability==limited


@pytest.mark.parametrize('student_id',['202612345','USER-42','ST0001'])
def test_professor_redaction_uses_issue_semantics_not_identifier_prefix(student_id):
    r=redact({'role':'professor'}, {'issues':[{'code':'STUDENT_OVERLAP','records':[student_id,'S1','S2']},
        {'code':'PREREQUISITE','records':[student_id,'S1']}],'adverse_students':[student_id]})
    assert student_id not in json.dumps(r)
    assert r['issues'][0]['records']==['S1','S2'] and r['issues'][0]['student_count']==1


def test_numeric_student_id_is_hidden_in_real_professor_preview(client):
    raw=generate().model_dump()
    raw['students'][0]['id']='202612345'
    sid=client.post('/api/import',json=raw).json()['id']
    client.post('/api/login',json={'username':'professor','password':'Mizan-demo-2026!'})
    r=client.post(f'/api/scenarios/{sid}/preview-change',json=dict(section_id='S001',meeting_index=0,day=0,start=600))
    assert r.status_code==200 and '202612345' not in r.text


def test_interpreted_unchanged_move_reports_invalid_baseline(client):
    row,data=scenario('diagnostic')
    s=data.sections[0];m=s.meetings[0]
    r=preview(data,row,dict(section_id=s.id,meeting_index=0,day=m.day,start=m.start,end=m.end),dict(day=m.day,start=m.start))
    assert r['unchanged'] and not r['feasible'] and r['existing_issue_count']>0

