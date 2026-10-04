import json
from fastapi import APIRouter,Depends,HTTPException
from pydantic import Field
from .models import StrictModel
from .main import user,require,scenario,STAFF
from . import local_model,agent_engine
from .store import connect

router=APIRouter(prefix='/api/agents')


class RunRequest(StrictModel):
    scenario_id:str
    request:str=Field(min_length=5,max_length=1500)
    max_changes:int=Field(default=5,ge=0,le=30)
    max_worsened:int=Field(default=0,ge=0,le=10000)
    solver_seconds:int=Field(default=15,ge=1,le=30)


@router.get('/status')
def status(u=Depends(user)):
    require(u,STAFF|{'hiring_manager','professor'})
    return dict(**local_model.status(),roles=agent_engine.ROLE_NAMES)


@router.post('/runs')
def start(body:RunRequest,u=Depends(user)):
    require(u,{'admin','registrar'})
    if not local_model.status()['available']:raise HTTPException(503,"Start the local model service before running agents")
    row,data=scenario(body.scenario_id)
    try:
        rid=agent_engine.schedule_run(body.scenario_id,row,data,body.request,body.model_dump(exclude={'scenario_id','request'}),u)
    except ValueError as error:raise HTTPException(409,str(error))
    return {'id':rid,'status':'queued'}


@router.get('/runs')
def runs(scenario_id:str,u=Depends(user)):
    require(u,STAFF)
    with connect() as con:
        rows=con.execute("SELECT * FROM agent_runs WHERE scenario_id=? ORDER BY created DESC LIMIT 30",(scenario_id,)).fetchall()
    return [dict(**{k:r[k] for k in r.keys() if k not in ['limits','result']},limits=json.loads(r['limits']),result=json.loads(r['result']) if r['result'] else None) for r in rows]


@router.get('/runs/{rid}')
def run(rid:str,u=Depends(user)):
    require(u,STAFF)
    with connect() as con:
        r=con.execute("SELECT * FROM agent_runs WHERE id=?",(rid,)).fetchone()
        if not r:raise HTTPException(404,"Agent run not found")
        events=con.execute("SELECT * FROM agent_events WHERE run_id=? ORDER BY id",(rid,)).fetchall()
    return dict(id=rid,status=r['status'],request=r['request'],revision=r['revision'],scenario_id=r['scenario_id'],
                result=json.loads(r['result']) if r['result'] else None,
                events=[dict(**{k:e[k] for k in e.keys() if k!='payload'},payload=json.loads(e['payload'])) for e in events])


@router.post('/runs/{rid}/cancel')
def cancel(rid:str,u=Depends(user)):
    require(u,{'admin','registrar'})
    with connect() as con:
        changed=con.execute("UPDATE agent_runs SET cancelled=1 WHERE id=? AND status IN ('queued','running')",(rid,)).rowcount
    if not changed:raise HTTPException(409,"Run is not active")
    return {'status':'cancellation_requested'}
