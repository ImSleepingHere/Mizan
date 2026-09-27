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

def queued_run(tmp_path,monkeypatch,name,limits):
    monkeypatch.setenv('MIZAN_DB',str(tmp_path/f'{name}.sqlite3'));init_db();ae.init_agents();row,data=scenario('baseline');rid=identifier()
    with connect() as con:con.execute('INSERT INTO agent_runs VALUES(?,?,?,?,?,?,?,?,?,?,?)',(rid,'baseline',1,'test',json.dumps(limits),'queued',None,now(),now(),'admin',0))
    monkeypatch.setattr(ae.local_model,'status',lambda:{'available':True,'coordinator_model':'test'})
    return rid,row,data

def scripted(role,ctx,actions):
    """Coordinator follows pending specialists; specialists run their tool when evidence is missing or a revision is required."""
    if role=='coordinator':
        pending=ctx['pending_specialists']
        return ae.Decision(action='delegate' if pending else 'finalize',agent=pending[0] if pending else 'student'),{}
    evidence=ctx['evidence']
    revise=role=='scheduling' and evidence.get('impact',{}).get('requires_revision')
    if 'report' in actions and role in evidence and not revise:return ae.Decision(action='report'),{}
    return ae.Decision(action=next(a for a in actions if a!='report'),max_changes=5),{}

def test_impact_review_drives_a_scheduling_revision(tmp_path,monkeypatch):
    """Spec §13.6: the first search yields no candidate, impact review requires a revision, scheduling reruns and impact re-checks."""
    limits={'max_changes':5,'max_worsened':0,'solver_seconds':5}
    rid,row,data=queued_run(tmp_path,monkeypatch,'revise',limits)
    real,searches=ae.optimize,[]
    def first_search_empty(d,m,s,rules=None):
        searches.append(m)
        if len(searches)==1:return {'status':'UNKNOWN','message':'No feasible improvement established; official timetable retained'}
        return real(d,m,s,rules=rules)
    monkeypatch.setattr(ae,'optimize',first_search_empty)
    monkeypatch.setattr(ae,'model_decision',scripted)
    ae.run_collaboration(rid,'baseline',row,data,'Reduce student gaps',limits,dict(username='admin',**USERS['admin']))
    with connect() as con:
        run=con.execute('SELECT * FROM agent_runs WHERE id=?',(rid,)).fetchone()
        tools=[r[0] for r in con.execute("SELECT action FROM agent_events WHERE run_id=? AND kind='tool_result' ORDER BY id",(rid,))]
        assert run['status']=='completed',run['result']
        search_at=[i for i,t in enumerate(tools) if t=='optimize_schedule'];review_at=[i for i,t in enumerate(tools) if t=='evaluate_change']
        assert len(search_at)==2 and len(review_at)==2
        assert search_at[0]<review_at[0]<search_at[1]<review_at[1]  # review between the two searches drove the revision
        result=json.loads(run['result'])
        assert result['disposition']=='recommend' and result['proposal_id']
        assert con.execute('SELECT status FROM proposals WHERE id=?',(result['proposal_id'],)).fetchone()[0]=='recommended'
        assert con.execute("SELECT revision FROM scenarios WHERE id='baseline'").fetchone()[0]==1  # nothing published

def test_budgets_stop_the_run_without_a_conclusion(tmp_path,monkeypatch):
    """Spec §13.7: a spent wall-clock budget, or a coordinator that never finalizes, ends as failed with no decision packet or proposal."""
    def never_finalizes(role,ctx,actions):
        if role=='coordinator':return ae.Decision(action='delegate',agent='student'),{}
        return scripted(role,ctx,actions)
    for name,limits in [('wall',{'max_changes':5,'max_worsened':0,'wall_seconds':0}),('rounds',{'max_changes':5,'max_worsened':0})]:
        rid,row,data=queued_run(tmp_path,monkeypatch,name,limits)
        monkeypatch.setattr(ae,'model_decision',never_finalizes)
        ae.run_collaboration(rid,'baseline',row,data,'test',limits,dict(username='admin',**USERS['admin']))
        with connect() as con:
            run=con.execute('SELECT * FROM agent_runs WHERE id=?',(rid,)).fetchone()
            assert run['status']=='failed',(name,run['result'])
            assert 'budget' in run['result'] or 'maximum collaboration rounds' in run['result']
            assert con.execute("SELECT count(*) FROM agent_events WHERE run_id=? AND kind='conclusion'",(rid,)).fetchone()[0]==0
            assert con.execute('SELECT count(*) FROM proposals').fetchone()[0]==0

