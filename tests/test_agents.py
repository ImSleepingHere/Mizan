import json
from backend import agent_engine as ae
from backend.store import init_db,connect,identifier,now
from backend.main import scenario,USERS

def test_agents_validate_before_proposal_and_do_not_publish(tmp_path,monkeypatch):
    monkeypatch.setenv('MIZAN_DB',str(tmp_path/'agents.sqlite3'));init_db();ae.init_agents();row,data=scenario('baseline');rid=identifier()
    limits={'max_changes':0,'max_worsened':0,'solver_seconds':1}
    with connect() as con:con.execute('INSERT INTO agent_runs VALUES(?,?,?,?,?,?,?,?,?,?,?)',(rid,'baseline',1,'test',json.dumps(limits),'queued',None,now(),now(),'admin',0))
    def decision(role,ctx,actions):
        if role=='coordinator':return ae.Decision(action='delegate' if ctx['pending_specialists'] else 'finalize',agent=ctx['pending_specialists'][0] if ctx['pending_specialists'] else 'student'),{}
        return ae.Decision(action=next(a for a in actions if a!='report'),max_changes=0),{}
    monkeypatch.setattr(ae,'model_decision',decision)
    ae.run_collaboration(rid,'baseline',row,data,'Review without changing sections',limits,dict(username='admin',**USERS['admin']))
    with connect() as con:
        run=con.execute('SELECT * FROM agent_runs WHERE id=?',(rid,)).fetchone()
        assert run['status']=='completed',run['result']
        assert json.loads(run['result'])['disposition']=='no_change'
        assert con.execute("SELECT revision FROM scenarios WHERE id='baseline'").fetchone()[0]==1
        assert con.execute('SELECT count(*) FROM proposals').fetchone()[0]==0

def test_cancelled_run_never_calls_model(tmp_path,monkeypatch):
    monkeypatch.setenv('MIZAN_DB',str(tmp_path/'cancel.sqlite3'));init_db();ae.init_agents();row,data=scenario('baseline');rid=identifier()
    with connect() as con:con.execute('INSERT INTO agent_runs VALUES(?,?,?,?,?,?,?,?,?,?,?)',(rid,'baseline',1,'test','{}','queued',None,now(),now(),'admin',1))
    def forbidden(*args):raise AssertionError('Model should not be called')
    monkeypatch.setattr(ae,'model_decision',forbidden)
    ae.run_collaboration(rid,'baseline',row,data,'test',{'max_changes':5,'max_worsened':0},dict(username='admin',**USERS['admin']))
    with connect() as con:assert con.execute('SELECT status FROM agent_runs WHERE id=?',(rid,)).fetchone()[0]=='cancelled'
