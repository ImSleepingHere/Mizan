import json
import os
import secrets
import time
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import Field
from .models import Semester, StrictModel, Window, Section, Policy
from .store import connect, init_db, audit, identifier, now, ROOT
from .analysis import validate, metrics, compare, student_metrics, eligible_students
from .solver import optimize, placement, workforce, options_for

USERS={"admin":dict(role="admin",name="Mizan Administrator"),"registrar":dict(role="registrar",name="Scheduling Committee"),
       "chair":dict(role="chair",name="Department Chair"),"professor":dict(role="professor",name="Dr. Faculty 01",professor_id="P001"),
       "hiring_manager":dict(role="hiring_manager",name="Hiring Manager"),
       "student":dict(role="student",name="Student 0001",student_id="ST0001")}
STAFF={"admin","registrar","chair"}


@asynccontextmanager
async def lifespan(app):
    init_db()
    from .agent_engine import init_agents
    init_agents()
    from .recruitment import init_recruitment
    init_recruitment()
    from .request_routes import init_requests
    init_requests()
    yield


app=FastAPI(title="MIZAN",version="0.2.0",lifespan=lifespan)


@app.middleware("http")
async def mutation_guard(request:Request,call_next):
    if request.url.path.startswith("/api/") and request.method not in ["GET","HEAD","OPTIONS"]:
        if request.headers.get("x-mizan-action")!="1":
            return Response('"Missing request guard"',status_code=403,media_type="application/json")
        origin=request.headers.get("origin")
        if origin and origin != str(request.base_url).rstrip("/"):
            return Response('"Cross-origin mutation rejected"',status_code=403,media_type="application/json")
    response=await call_next(request)
    response.headers["X-Content-Type-Options"]="nosniff"
    response.headers["Referrer-Policy"]="same-origin"
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"]="no-store"
    return response


def user(request:Request):
    token=request.cookies.get("mizan_session","")
    with connect() as con:
        session=con.execute("SELECT username FROM sessions WHERE token=? AND expires>?",(token,time.time())).fetchone()
    if not session or session["username"] not in USERS:
        raise HTTPException(401,"Sign in to Mizan")
    return dict(username=session["username"],**USERS[session["username"]])


def require(u,roles):
    if u["role"] not in roles:
        raise HTTPException(403,"This action is not available to your role")


def scenario(sid):
    with connect() as con:
        row=con.execute("SELECT * FROM scenarios WHERE id=?",(sid,)).fetchone()
    if not row:
        raise HTTPException(404,"Scenario not found")
    return dict(row),Semester.model_validate_json(row["data"])


def redact(u,obj):
    """Professors see aggregate student counts only (spec §18.3): no student identities in any response."""
    if u["role"]!="professor":
        return obj
    def walk(x):
        if isinstance(x,dict):
            out={}
            for k,v in x.items():
                if k=="adverse_students":
                    out["adverse_count"]=len(v)
                elif k=="records" and isinstance(v,list):
                    out[k]=[r for r in v if not str(r).startswith("ST")]
                    hidden=len(v)-len(out[k])
                    if hidden: out["student_count"]=hidden
                else:
                    out[k]=walk(v)
            return out
        if isinstance(x,list):
            return [walk(v) for v in x]
        return x
    return walk(obj)


def own_sections(u,data):
    return {s.id for s in data.sections if u["role"]=="professor" and s.professor_id==u.get("professor_id")}


def save_proposal(sid,row,data,kind,analysis,u,reason=""):
    pid=identifier()
    issues=validate(data)
    analysis.update(issues=issues[:250],conflict_count=len(issues))
    baseline=Semester.model_validate_json(row["data"])
    summary_keys=["gap_hours","average_days","score","long_gap_2h","worst_decile_gap_hours","load_gini","room_utilization"]
    before,after=metrics(baseline),metrics(data,issues)
    analysis["before_metrics"]={k:before[k] for k in summary_keys}
    analysis["after_metrics"]={k:after[k] for k in summary_keys}
    state="invalid" if issues else "recommended"
    with connect() as con:
        con.execute("INSERT INTO proposals VALUES(?,?,?,?,?,?,?,?,?,?)",(pid,sid,row["revision"],kind,state,data.model_dump_json(),json.dumps(analysis,ensure_ascii=False),now(),u["username"],reason))
        audit(con,u["username"],"proposal_created",pid,dict(kind=kind,status=state,scenario_id=sid))
    return dict(id=pid,status=state,analysis=analysis)


class Login(StrictModel):
    username:str
    password:str


@app.post("/api/login")
def login(body:Login,response:Response):
    password=os.environ.get("MIZAN_DEMO_PASSWORD","Mizan-demo-2026!")
    if body.username not in USERS or not secrets.compare_digest(body.password,password):
        raise HTTPException(401,"Incorrect demo account or password")
    token=secrets.token_urlsafe(32)
    with connect() as con:
        con.execute("DELETE FROM sessions WHERE expires<?",(time.time(),))
        con.execute("INSERT INTO sessions VALUES(?,?,?)",(token,body.username,time.time()+8*3600))
    response.set_cookie("mizan_session",token,httponly=True,samesite="strict",max_age=8*3600)
    return dict(username=body.username,**USERS[body.username])


@app.post("/api/logout")
def logout(request:Request,response:Response):
    with connect() as con:
        con.execute("DELETE FROM sessions WHERE token=?",(request.cookies.get("mizan_session",""),))
    response.delete_cookie("mizan_session")
    return {"ok":True}


@app.get("/api/me")
def me(u=Depends(user)):
    return u


@app.get("/api/health")
def health():
    return dict(status="ok",version="0.2.0",mode="local_demo",agents="local_model")


@app.get("/api/scenarios")
def scenarios(u=Depends(user)):
    with connect() as con:
        return [dict(r) for r in con.execute("SELECT id,name,revision FROM scenarios ORDER BY rowid")]


@app.get("/api/scenarios/{sid}")
def get_scenario(sid:str,u=Depends(user)):
    row,data=scenario(sid)
    if u["role"]=="hiring_manager":
        return dict(id=sid,revision=row["revision"],name=data.name,kind=data.kind,policy=data.policy.model_dump(),students=[],professors=[],sections=[],courses=[],rooms=[])
    if u["role"]=="student":
        student=next((s for s in data.students if s.id==u["student_id"]),None)
        if not student: raise HTTPException(404,"Student not in this scenario")
        sections=[s for s in data.sections if s.id in student.sections]
        personal=next(s for s in student_metrics(data) if s["id"]==student.id)
        if any(set(i["records"]) & ({student.id}|set(student.sections)) for i in validate(data)):
            personal["score"]=None
        return dict(id=sid,revision=row["revision"],name=data.name,provenance=data.provenance,students=[student.model_dump()],
                    sections=[s.model_dump() for s in sections],courses=[c.model_dump() for c in data.courses],
                    rooms=[r.model_dump() for r in data.rooms],professors=[],policy=data.policy.model_dump(),kind=data.kind,
                    personal_metrics=personal)
    if u["role"]=="professor":
        sections=[s for s in data.sections if s.professor_id==u["professor_id"]]
        return dict(id=sid,revision=row["revision"],**data.model_copy(update=dict(sections=sections,students=[],demands=[],professors=[p for p in data.professors if p.id==u["professor_id"]])).model_dump())
    require(u,STAFF)
    return dict(id=sid,revision=row["revision"],**data.model_dump())


@app.get("/api/scenarios/{sid}/metrics")
def get_metrics(sid:str,u=Depends(user)):
    require(u,STAFF)
    _,data=scenario(sid)
    return metrics(data)


@app.get("/api/scenarios/{sid}/export")
def export(sid:str,u=Depends(user)):
    require(u,STAFF)
    _,data=scenario(sid)
    return Response(data.model_dump_json(indent=2),media_type="application/json",headers={"Content-Disposition":f'attachment; filename="mizan-{sid}.json"'})


@app.post("/api/import")
def import_semester(body:Semester,u=Depends(user)):
    require(u,{"admin","registrar"})
    if len(body.students)>10000 or len(body.sections)>1000:
        raise HTTPException(422,"Local import limit: 10,000 students and 1,000 sections")
    sid=identifier()
    with connect() as con:
        con.execute("INSERT INTO scenarios VALUES(?,?,?,?)",(sid,body.name,1,body.model_dump_json()))
        con.execute("INSERT INTO versions VALUES(?,?,?,?)",(sid,1,body.model_dump_json(),now()))
        audit(con,u["username"],"import",sid,{"provenance":body.provenance})
    return dict(id=sid,issues=validate(body)[:100])


class OptimizeRequest(StrictModel):
    max_changes:int=Field(default=5,ge=0,le=30)
    seconds:int=Field(default=10,ge=1,le=60)


@app.post("/api/scenarios/{sid}/optimize")
def run_optimize(sid:str,body:OptimizeRequest,u=Depends(user)):
    require(u,{"admin","registrar","professor"})
    row,data=scenario(sid)
    movable=None
    if u["role"]=="professor":
        # "My classes" scope (spec §18.3): only own sections may move; every other section is fixed in the search.
        movable=own_sections(u,data)
        if not movable: raise HTTPException(403,"You have no sections in this timetable")
    max_changes=min(body.max_changes,len(movable)) if movable is not None else body.max_changes
    result=optimize(data,max_changes,body.seconds,movable=movable)
    result.update(scope="own" if movable is not None else "semester",max_changes_used=max_changes)
    candidate=result.pop("candidate",None)
    if not candidate or not result["comparison"]["changes"]:
        return redact(u,result)
    kind="optimization" if movable is None else "own_optimization"
    return redact(u,dict(**result,proposal=save_proposal(sid,row,Semester.model_validate(candidate),kind,dict(result),u)))


class ChangeRequest(StrictModel):
    section_id:str
    meeting_index:int=Field(default=0,ge=0)
    day:int=Field(ge=0,le=4)
    start:int=Field(ge=0,lt=1440)
    reason:str=Field(min_length=3,max_length=1000)


@app.post("/api/scenarios/{sid}/changes")
def change(sid:str,body:ChangeRequest,u=Depends(user)):
    require(u,{"admin","registrar","professor"})
    row,data=scenario(sid)
    original=next((s for s in data.sections if s.id==body.section_id),None)
    if not original or body.meeting_index>=len(original.meetings): raise HTTPException(404,"Meeting not found")
    if u["role"]=="professor" and original.professor_id!=u["professor_id"]: raise HTTPException(403,"Only your own sections may be proposed")
    candidate=data.model_copy(deep=True)
    section=next(s for s in candidate.sections if s.id==body.section_id)
    duration=section.meetings[body.meeting_index].end-section.meetings[body.meeting_index].start
    if body.start+duration>1440: raise HTTPException(422,"Meeting extends past midnight")
    section.meetings[body.meeting_index]=Window(day=body.day,start=body.start,end=body.start+duration)
    analysis=dict(comparison=compare(data,candidate))
    alternatives=[]
    if validate(candidate):
        for option in options_for(data,original,room_limit=1):
            if option==original: continue
            alternative=data.model_copy(deep=True)
            alternative.sections=[option if s.id==original.id else s for s in alternative.sections]
            if not validate(alternative):
                diff=compare(data,alternative)
                alternatives.append(dict(section=option.model_dump(),recovered_hours=diff["recovered_hours"],worsened=diff["worsened"]))
        alternatives.sort(key=lambda a:(a["worsened"],-a["recovered_hours"]))
    analysis["alternatives"]=alternatives[:3]
    return redact(u,save_proposal(sid,row,candidate,"change",analysis,u,body.reason))


class PreviewRequest(StrictModel):
    section_id:str
    meeting_index:int=Field(default=0,ge=0)
    day:int=Field(ge=0,le=4)
    start:int=Field(ge=0,lt=1440)


_BASELINE_ISSUES={}


def baseline_issue_keys(sid,row,data):
    key=(sid,row["revision"])
    if key not in _BASELINE_ISSUES:
        if len(_BASELINE_ISSUES)>16:_BASELINE_ISSUES.clear()
        _BASELINE_ISSUES[key]={(i["code"],tuple(i["records"])) for i in validate(data)}
    return _BASELINE_ISSUES[key]


@app.post("/api/scenarios/{sid}/preview-change")
def preview_change(sid:str,body:PreviewRequest,u=Depends(user)):
    """Evaluate a proposed meeting move without saving anything. Used by the interactive timetable."""
    require(u,{"admin","registrar","professor"})
    row,data=scenario(sid)
    original=next((s for s in data.sections if s.id==body.section_id),None)
    if not original or body.meeting_index>=len(original.meetings): raise HTTPException(404,"Meeting not found")
    if u["role"]=="professor" and original.professor_id!=u["professor_id"]: raise HTTPException(403,"Only your own sections may be proposed")
    candidate=data.model_copy(deep=True)
    section=next(s for s in candidate.sections if s.id==body.section_id)
    current=section.meetings[body.meeting_index]
    duration=current.end-current.start
    if body.start+duration>1440: raise HTTPException(422,"Meeting extends past midnight")
    section.meetings[body.meeting_index]=Window(day=body.day,start=body.start,end=body.start+duration)
    existing=baseline_issue_keys(sid,row,data)
    issues=validate(candidate)
    introduced=[i for i in issues if (i["code"],tuple(i["records"])) not in existing]
    diff=compare(data,candidate)
    return redact(u,dict(revision=row["revision"],section_id=body.section_id,meeting_index=body.meeting_index,day=body.day,start=body.start,end=body.start+duration,
                feasible=not introduced,new_issues=introduced[:20],new_issue_count=len(introduced),existing_issue_count=len(existing),
                recovered_hours=diff["recovered_hours"],benefiting=diff["benefiting"],worsened=diff["worsened"],
                worst_increase_minutes=diff["worst_increase_minutes"]))


@app.get("/api/scenarios/{sid}/my-classes")
def my_classes(sid:str,u=Depends(user)):
    """A professor's own sections with aggregate figures for their students only (no identities)."""
    require(u,{"professor"})
    row,data=scenario(sid)
    mine=own_sections(u,data)
    sections=[s for s in data.sections if s.id in mine]
    roster={s.id:[st for st in data.students if s.id in st.sections] for s in sections}
    students={st.id:st for ids in roster.values() for st in ids}
    personal={m["id"]:m for m in student_metrics(data) if m["id"] in students}
    issues=[i for i in validate(data) if set(i["records"])&mine]
    n=max(1,len(personal))
    return dict(revision=row["revision"],sections=[dict(**s.model_dump(),enrolled=len(roster[s.id])) for s in sections],
                students=len(personal),average_gap_hours=round(sum(p["gap_minutes"] for p in personal.values())/n/60,2),
                average_campus_days=round(sum(p["campus_days"] for p in personal.values())/n,2),
                long_gap_2h=sum(p["longest_gap"]>=120 for p in personal.values()),
                teaching_minutes=sum(m.end-m.start for s in sections for m in s.meetings),
                contracted_minutes=next((p.contracted_minutes for p in data.professors if p.id==u.get("professor_id")),None),
                conflicts=len(issues),note="Aggregates cover students enrolled in at least one of your sections.")


class SlotRequest(StrictModel):
    sections:list[str]=Field(min_length=1,max_length=10)
    duration:int=Field(ge=15,le=240)
    days:list[int]=[]
    same_time_for_all:bool=False
    merge:bool=False
    earliest:int|None=Field(default=None,ge=0,le=1440)
    latest_end:int|None=Field(default=None,ge=0,le=1440)


def find_slots(u,data,body:SlotRequest):
    from .solver import common_slots
    known={s.id for s in data.sections}
    if not set(body.sections)<=known: raise HTTPException(404,"Section not found")
    if u["role"]=="professor" and not set(body.sections)<=own_sections(u,data): raise HTTPException(403,"Only your own sections")
    if body.merge and len(set(body.sections))<2: raise HTTPException(422,"A merge needs at least two sections")
    if any(d not in range(5) for d in body.days): raise HTTPException(422,"Unknown day")
    return redact(u,common_slots(data,list(dict.fromkeys(body.sections)),body.duration,body.days or None,body.same_time_for_all,body.merge,
                                 body.earliest,body.latest_end))


@app.post("/api/scenarios/{sid}/free-slots")
def free_slots(sid:str,body:SlotRequest,u=Depends(user)):
    """Scheduling tool: ranked common free slots for the students of the given sections (read-only)."""
    require(u,{"admin","registrar","chair","professor"})
    _,data=scenario(sid)
    result=find_slots(u,data,body)
    with connect() as con:
        audit(con,u["username"],"free_slot_search",sid,body.model_dump())
    return result


class Alternative(StrictModel):
    section:Section
    reason:str="Feasible alternative to the requested move"


@app.post("/api/scenarios/{sid}/alternative")
def alternative(sid:str,body:Alternative,u=Depends(user)):
    require(u,{"admin","registrar","professor"})
    row,data=scenario(sid)
    existing=next((s for s in data.sections if s.id==body.section.id),None)
    if not existing: raise HTTPException(404,"Section not found")
    if u["role"]=="professor" and existing.professor_id!=u["professor_id"]: raise HTTPException(403,"Not your section")
    if (body.section.course_id,body.section.professor_id,body.section.capacity)!=(existing.course_id,existing.professor_id,existing.capacity):
        raise HTTPException(422,"Only meeting times and room may change")
    if body.section.room_id not in {r.id for r in data.rooms}: raise HTTPException(422,"Unknown room")
    candidate=data.model_copy(deep=True)
    candidate.sections=[body.section if s.id==existing.id else s for s in candidate.sections]
    return redact(u,save_proposal(sid,row,candidate,"change",dict(comparison=compare(data,candidate)),u,body.reason))


@app.get("/api/scenarios/{sid}/placement/{course_id}")
def get_placement(sid:str,course_id:str,u=Depends(user)):
    require(u,STAFF)
    _,data=scenario(sid)
    if course_id not in {c.id for c in data.courses}: raise HTTPException(404,"Course not found")
    return placement(data,course_id)


class PlaceRequest(StrictModel):
    course_id:str
    option_index:int=Field(ge=0,le=14)


@app.post("/api/scenarios/{sid}/placement")
def propose_placement(sid:str,body:PlaceRequest,u=Depends(user)):
    require(u,{"admin","registrar"})
    row,data=scenario(sid)
    if body.course_id not in {c.id for c in data.courses}: raise HTTPException(404,"Course not found")
    choices=placement(data,body.course_id)["options"]
    if body.option_index>=len(choices): raise HTTPException(422,"Placement is no longer available")
    selected=choices[body.option_index]
    candidate=data.model_copy(deep=True)
    section=Section(id="NEW-"+identifier()[:6],course_id=body.course_id,professor_id=selected["professor_id"],room_id=selected["room_id"],capacity=selected["capacity"],meetings=selected["meetings"])
    candidate.sections.append(section)
    return save_proposal(sid,row,candidate,"placement",dict(comparison=compare(data,candidate),placement=selected),u,"Additional section; enrollment is a separate staff action")


@app.get("/api/scenarios/{sid}/eligible")
def eligible(sid:str,u=Depends(user)):
    require(u,{"student"})
    _,data=scenario(sid)
    from .analysis import overlaps
    student=next((s for s in data.students if s.id==u["student_id"]),None)
    if not student: raise HTTPException(404,"Student not found")
    current=[m for s in data.sections if s.id in student.sections for m in s.meetings]
    result=[]
    for c in data.courses:
        if any(s.id==student.id for s in eligible_students(data,c.id)):
            for s in data.sections:
                if s.course_id==c.id and not any(overlaps(a,b) for a in current for b in s.meetings):
                    seats=s.capacity-sum(s.id in st.sections for st in data.students)
                    if seats>0: result.append(dict(section_id=s.id,course=c.model_dump(),seats=seats,meetings=[m.model_dump() for m in s.meetings]))
    return result


@app.get("/api/proposals")
def proposals(scenario_id:str,u=Depends(user)):
    require(u,STAFF|{"professor"})
    with connect() as con:
        rows=con.execute("SELECT id,scenario_id,base_revision,kind,status,analysis,created,actor,reason FROM proposals WHERE scenario_id=? ORDER BY created DESC",(scenario_id,)).fetchall()
    return redact(u,[dict(**{k:r[k] for k in r.keys() if k!="analysis"},analysis=json.loads(r["analysis"])) for r in rows if u["role"]!="professor" or r["actor"]==u["username"]])


@app.post("/api/proposals/{pid}/{action}")
def decide(pid:str,action:str,u=Depends(user)):
    require(u,{"admin","registrar"})
    if action not in {"approve","reject","publish"}: raise HTTPException(404,"Unknown action")
    with connect() as con:
        con.execute("BEGIN IMMEDIATE")
        proposal=con.execute("SELECT * FROM proposals WHERE id=?",(pid,)).fetchone()
        if not proposal: raise HTTPException(404,"Proposal not found")
        current=con.execute("SELECT * FROM scenarios WHERE id=?",(proposal["scenario_id"],)).fetchone()
        if action=="reject":
            if proposal["status"] not in {"recommended","approved","invalid"}: raise HTTPException(409,"Proposal cannot be rejected in this state")
            status="rejected"
        else:
            expected="recommended" if action=="approve" else "approved"
            if proposal["status"]!=expected: raise HTTPException(409,f"Proposal must be {expected}")
            if current["revision"]!=proposal["base_revision"]: raise HTTPException(409,"Stale proposal: timetable changed. Evaluate a new proposal.")
            data=Semester.model_validate_json(proposal["data"])
            if validate(data): raise HTTPException(422,"Hard constraints failed; publication blocked")
            status="approved" if action=="approve" else "published"
            if action=="publish":
                revision=current["revision"]+1
                con.execute("UPDATE scenarios SET revision=?,data=? WHERE id=?",(revision,proposal["data"],proposal["scenario_id"]))
                con.execute("INSERT INTO versions VALUES(?,?,?,?)",(proposal["scenario_id"],revision,proposal["data"],now()))
        con.execute("UPDATE proposals SET status=? WHERE id=?",(status,pid))
        audit(con,u["username"],action,pid,{"scenario_id":proposal["scenario_id"],"base_revision":proposal["base_revision"]})
    return {"status":status}


@app.get("/api/scenarios/{sid}/workforce")
def get_workforce(sid:str,u=Depends(user)):
    require(u,STAFF)
    _,data=scenario(sid)
    return workforce(data)


class RequisitionRequest(StrictModel):
    demand_id:str


@app.post("/api/scenarios/{sid}/requisitions")
def requisition(sid:str,body:RequisitionRequest,u=Depends(user)):
    require(u,{"admin","chair"})
    row,data=scenario(sid)
    signal=next((s for s in workforce(data)["signals"] if s["demand_id"]==body.demand_id),None)
    if not signal or signal["status"]!="PROVEN_CAPACITY_SHORTFALL": raise HTTPException(422,"No proven staffing shortage for this demand")
    rid=identifier()
    with connect() as con:
        con.execute("INSERT INTO requisitions VALUES(?,?,?,?,?,?)",(rid,sid,row["revision"],"draft",json.dumps(signal),now()))
        audit(con,u["username"],"requisition_created",rid,signal)
    return {"id":rid,"status":"draft"}


@app.get("/api/requisitions")
def requisitions(u=Depends(user)):
    require(u,STAFF|{"hiring_manager"})
    with connect() as con:
        return [dict(id=r["id"],scenario_id=r["scenario_id"],revision=r["revision"],status=r["status"],created=r["created"],data=json.loads(r["data"])) for r in con.execute("SELECT * FROM requisitions ORDER BY created DESC")]


@app.get("/api/audit")
def get_audit(u=Depends(user)):
    require(u,STAFF)
    with connect() as con:
        return [dict(r) for r in con.execute("SELECT * FROM audit ORDER BY id DESC LIMIT 100")]


class PolicyUpdate(StrictModel):
    revision:int
    policy:Policy


@app.post("/api/scenarios/{sid}/policy")
def update_policy(sid:str,body:PolicyUpdate,u=Depends(user)):
    require(u,{"admin"})
    with connect() as con:
        con.execute("BEGIN IMMEDIATE")
        row=con.execute("SELECT * FROM scenarios WHERE id=?",(sid,)).fetchone()
        if not row: raise HTTPException(404,"Scenario not found")
        if row["revision"]!=body.revision: raise HTTPException(409,"Policy is stale; refresh first")
        data=Semester.model_validate_json(row["data"])
        data.policy=body.policy.model_copy(update={"version":str(row["revision"]+1)})
        payload=data.model_dump_json()
        con.execute("UPDATE scenarios SET revision=revision+1,data=? WHERE id=?",(payload,sid))
        con.execute("INSERT INTO versions VALUES(?,?,?,?)",(sid,row["revision"]+1,payload,now()))
        audit(con,u["username"],"policy_updated",sid,data.policy.model_dump())
    return {"revision":row["revision"]+1,"issues":validate(data)[:50]}


from .agent_routes import router as agent_router
app.include_router(agent_router)
from .recruitment import router as recruitment_router
app.include_router(recruitment_router)
from .request_routes import router as request_router
app.include_router(request_router)

DIST=ROOT/"frontend"/"dist"
if DIST.exists():
    app.mount("/assets",StaticFiles(directory=DIST/"assets"),name="assets")


@app.get("/{path:path}")
def frontend(path:str):
    if path.startswith("api/"): raise HTTPException(404,"API route not found")
    if not (DIST/"index.html").exists(): raise HTTPException(503,"Build the frontend first")
    return FileResponse(DIST/"index.html")
