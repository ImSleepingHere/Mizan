"""Independent checks for alternative objectives and the human decision boundary."""
import copy
import json
import math
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.fixtures import generate
from backend.models import Semester
from backend.analysis import validate, compare, metrics, student_metrics
from backend.solver import optimize
from backend.store import connect
from backend import plan_routes


@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setenv("MIZAN_DB",str(tmp_path/"plans.sqlite3"))
    monkeypatch.delenv("MIZAN_DEMO_PASSWORD",raising=False)
    with TestClient(app,headers={"X-Mizan-Action":"1"}) as c:
        login(c,"admin")
        raw=generate(groups=2,per_group=3).model_dump()
        c.sid=c.post("/api/import",json=raw).json()["id"]
        yield c


def login(c,name):
    assert c.post('/api/login',json=dict(username=name,password='Mizan-demo-2026!')).status_code==200


def search(c,**overrides):
    r=c.post(f'/api/scenarios/{c.sid}/plan-comparisons',json=dict(revision=1,max_changes=3,seconds=2,**overrides))
    assert r.status_code==200,r.text
    return r.json()


@pytest.mark.parametrize('strategy',plan_routes.STRATEGIES)
def test_each_objective_returns_independently_valid_improvement(strategy):
    data=generate(groups=2,per_group=3)
    before=data.model_dump()
    r=optimize(data,3,3,strategy=strategy)
    assert r['status'] in {'OPTIMAL','FEASIBLE'}
    candidate=Semester.model_validate(r['candidate'])
    assert validate(candidate)==[]
    assert compare(data,candidate)==r['comparison']
    assert 0<len(r['comparison']['changes'])<=3
    saved=sum(s['gap_minutes'] for s in student_metrics(data))-sum(s['gap_minutes'] for s in student_metrics(candidate))
    assert saved>=math.ceil(sum(s['gap_minutes'] for s in student_metrics(data))*.01)
    assert data.model_dump()==before  # no policy or timetable mutation


def test_fewest_changes_really_prefers_one_change():
    data=generate(groups=2,per_group=3)
    least=optimize(data,5,3,strategy='fewest_changes')
    most=optimize(data,5,3,strategy='time_saved')
    assert least['status']=='OPTIMAL' and len(least['comparison']['changes'])==1
    assert most['comparison']['recovered_hours']>least['comparison']['recovered_hours']


def test_balanced_spreads_relief_instead_of_only_maximizing_total_savings():
    data=generate(groups=4,per_group=3)
    most=optimize(data,3,3,strategy='time_saved')
    balanced=optimize(data,3,3,strategy='balanced')
    assert most['status']=='OPTIMAL' and balanced['status']=='OPTIMAL'
    assert balanced['comparison']['benefiting']>most['comparison']['benefiting']
    def square_burden(result):
        candidate=Semester.model_validate(result['candidate'])
        return sum(s['gap_minutes']**2 for s in student_metrics(candidate))
    assert square_burden(balanced)<square_burden(most)


def test_policy_change_blocks_selection_of_saved_plan(client):
    result=search(client)
    data=client.get(f'/api/scenarios/{client.sid}').json()
    assert client.post(f'/api/scenarios/{client.sid}/policy',json=dict(revision=1,policy=data['policy'])).status_code==200
    assert client.post(f"/api/plan-comparisons/{result['id']}/time_saved/select",json={}).status_code==409


def test_imported_plans_keep_publish_readiness_guard(client):
    rows=[dict(code='MKT 201',section='12',days=[0,2],start=480,end=540,room='A1'),
          dict(code='FIN 202',section='17',days=[0,2],start=780,end=840,room='A2')]
    sid=client.post('/api/edugate/import',json=dict(student_id='T1',student_name='Invented',rows=rows)).json()['id']
    r=client.post(f'/api/scenarios/{sid}/plan-comparisons',json=dict(revision=1,max_changes=2,seconds=2)).json()
    assert r['imported'] and any(p['available'] for p in r['plans'])
    key=next(p['key'] for p in r['plans'] if p['available'])
    p=client.post(f"/api/plan-comparisons/{r['id']}/{key}/select",json={}).json()
    assert client.post(f"/api/proposals/{p['id']}/approve",json={}).status_code==200
    assert client.post(f"/api/proposals/{p['id']}/publish",json={}).status_code==409


def test_comparison_is_read_only_and_survives_reload(client):
    result=search(client)
    assert len(result['plans'])==3 and result['base_revision']==1 and not result['stale']
    assert all('candidate' not in p for p in result['plans'])
    with connect() as con:
        assert con.execute('SELECT count(*) FROM proposals').fetchone()[0]==0
        assert con.execute('SELECT revision FROM scenarios WHERE id=?',(client.sid,)).fetchone()[0]==1
        payload=json.loads(con.execute('SELECT data FROM plan_comparisons WHERE id=?',(result['id'],)).fetchone()[0])
    assert client.get(f'/api/scenarios/{client.sid}/plan-comparisons').json()['id']==result['id']
    for p in payload['plans']:
        if p['available']:
            candidate=Semester.model_validate(p['candidate'])
            assert validate(candidate)==[] and p['after']==metrics(candidate)


def test_selection_approval_publication_and_sibling_staleness(client):
    result=search(client)
    key=next(p['key'] for p in result['plans'] if p['available'])
    url=f"/api/plan-comparisons/{result['id']}/{key}/select"
    selected=client.post(url,json={}).json()
    assert selected['status']=='recommended'
    assert client.post(url,json={}).json()['id']==selected['id']
    assert client.get(f'/api/scenarios/{client.sid}').json()['revision']==1
    assert client.post(f"/api/proposals/{selected['id']}/publish",json={}).status_code==409
    assert client.post(f"/api/proposals/{selected['id']}/approve",json={}).status_code==200
    assert client.post(f"/api/proposals/{selected['id']}/publish",json={}).status_code==200
    assert client.post(url,json={}).status_code==409
    assert client.get(f'/api/scenarios/{client.sid}/plan-comparisons').json()['stale']


@pytest.mark.parametrize('role',['student','professor','hiring_manager','chair'])
def test_roles_cannot_generate_or_select(role,client):
    result=search(client)
    login(client,role)
    assert client.post(f'/api/scenarios/{client.sid}/plan-comparisons',json=dict(revision=1)).status_code==403
    assert client.post(f"/api/plan-comparisons/{result['id']}/time_saved/select",json={}).status_code==403
    assert client.get(f'/api/scenarios/{client.sid}/plan-comparisons').status_code==(200 if role=='chair' else 403)


def test_registrar_can_select_and_missing_guard_is_rejected(client):
    result=search(client)
    login(client,'registrar')
    assert client.post(f"/api/plan-comparisons/{result['id']}/time_saved/select",json={}).status_code==200
    assert client.post(f'/api/scenarios/{client.sid}/plan-comparisons',json=dict(revision=1),headers={'X-Mizan-Action':'0'}).status_code==403


def test_invalid_stale_and_invalid_limits(client):
    assert client.post('/api/scenarios/diagnostic/plan-comparisons',json=dict(revision=1)).status_code==422
    assert client.post(f'/api/scenarios/{client.sid}/plan-comparisons',json=dict(revision=2)).status_code==409
    for fields in [dict(seconds=0),dict(seconds=31),dict(max_changes=31),dict(revision=0)]:
        body=dict(revision=1);body.update(fields)
        assert client.post(f'/api/scenarios/{client.sid}/plan-comparisons',json=body).status_code==422


def test_no_feasible_plan_cannot_be_selected(client,monkeypatch):
    monkeypatch.setattr(plan_routes,'optimize',lambda *a,**kw:dict(status='UNKNOWN',runtime=.01))
    r=search(client)
    assert r['distinct_plans']==0 and not any(p['available'] for p in r['plans'])
    assert client.post(f"/api/plan-comparisons/{r['id']}/time_saved/select",json={}).status_code==409
    assert client.post(f"/api/plan-comparisons/{r['id']}/invented/select",json={}).status_code==404
    assert client.post('/api/plan-comparisons/missing/time_saved/select',json={}).status_code==404


def test_identical_results_are_disclosed_and_share_one_proposal(client,monkeypatch):
    same=optimize(generate(groups=2,per_group=3),1,2,strategy='time_saved')
    monkeypatch.setattr(plan_routes,'optimize',lambda *a,**kw:copy.deepcopy(same))
    r=search(client)
    assert r['distinct_plans']==1
    assert [p['same_as'] for p in r['plans']]==[None,'time_saved','time_saved']
    ids=[client.post(f"/api/plan-comparisons/{r['id']}/{p['key']}/select",json={}).json()['id'] for p in r['plans']]
    assert len(set(ids))==1


def test_invalid_candidate_is_not_exposed_even_if_solver_claims_feasible(client,monkeypatch):
    data=generate(groups=2,per_group=3);data.sections[0].meetings[0].end+=5
    monkeypatch.setattr(plan_routes,'optimize',lambda *a,**kw:dict(status='FEASIBLE',candidate=data.model_dump()))
    r=search(client)
    assert r['distinct_plans']==0 and all(p['status']=='VALIDATION_FAILED' for p in r['plans'])


def test_zero_move_budget_and_zero_gap_timetable_do_not_fabricate_improvement():
    data=generate(groups=1,per_group=1)
    for strategy in plan_routes.STRATEGIES:
        r=optimize(data,0,1,strategy=strategy)
        assert r['status']=='INFEASIBLE' and 'candidate' not in r
    data.students=[]
    assert optimize(data,3,1,strategy='balanced')['status']=='INFEASIBLE'
