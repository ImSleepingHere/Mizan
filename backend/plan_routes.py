"""Three independent, validated choices from one immutable timetable version.

Search never saves proposals. A committee member explicitly selects a stored
candidate, which then follows the normal approve -> publish gate.
"""
import hashlib
import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import Field
from .main import user, require, scenario, STAFF
from .models import StrictModel, Semester
from .analysis import metrics, validate, compare
from .solver import optimize
from .store import connect, identifier, now, audit

router = APIRouter(prefix="/api")
STRATEGIES = ("time_saved", "fewest_changes", "balanced")


def init_plans():
    with connect() as con:
        con.execute('''CREATE TABLE IF NOT EXISTS plan_comparisons(
            id TEXT PRIMARY KEY, scenario_id TEXT NOT NULL, base_revision INTEGER NOT NULL,
            data TEXT NOT NULL, created TEXT NOT NULL, actor TEXT NOT NULL)''')


class CompareInput(StrictModel):
    revision: int = Field(ge=1)
    max_changes: int = Field(default=5, ge=0, le=30)
    seconds: int = Field(default=15, ge=1, le=30)


def fingerprint(data):
    # IDs, instructor, room, capacity and meetings: genuine timetable identity.
    sections = sorted((s.model_dump() for s in data.sections), key=lambda s:s["id"])
    return hashlib.sha256(json.dumps(sections,sort_keys=True).encode()).hexdigest()


def present(row, current_revision):
    data = json.loads(row["data"])
    plans = [{k:v for k,v in plan.items() if k != "candidate"} for plan in data["plans"]]
    return dict(id=row["id"], scenario_id=row["scenario_id"], base_revision=row["base_revision"],
                current_revision=current_revision, stale=row["base_revision"]!=current_revision,
                created=row["created"], before=data["before"], plans=plans,
                limits=data["limits"], distinct_plans=data["distinct_plans"],
                imported=data["imported"])


@router.post("/scenarios/{sid}/plan-comparisons")
def generate_plans(sid: str, body: CompareInput, u=Depends(user)):
    require(u, {"admin","registrar"})
    row, data = scenario(sid)
    if row["revision"] != body.revision:
        raise HTTPException(409,"Stale proposal: timetable changed. Refresh before comparing plans.")
    before = metrics(data)
    if not before["valid"]:
        raise HTTPException(422,"Resolve hard violations before optimization")
    plans, seen = [], {}
    for strategy in STRATEGIES:
        result = optimize(data,body.max_changes,body.seconds,strategy=strategy)
        raw = result.pop("candidate",None)
        plan = dict(key=strategy, status=result["status"], runtime=result.get("runtime",0),
                    search_scope=result.get("search_scope"), candidate=None, same_as=None,
                    available=False, proposal_id=None, minimum_saved_minutes=result.get("minimum_saved_minutes"))
        if raw:
            candidate = Semester.model_validate(raw)
            issues = validate(candidate)
            diff = compare(data,candidate)
            # Recheck independently at the boundary; never expose an invalid plan.
            if not issues and diff["changes"] and diff["recovered_hours"] > 0:
                digest = fingerprint(candidate)
                plan.update(candidate=raw,available=True,comparison=diff,after=metrics(candidate,issues),
                            same_as=seen.get(digest), conflict_count=0)
                seen.setdefault(digest,strategy)
            else:
                plan["status"] = "VALIDATION_FAILED" if issues else "NO_IMPROVEMENT"
        plans.append(plan)
    payload = dict(before=before,plans=plans,limits=body.model_dump(),distinct_plans=len(seen),imported=data.kind=="edugate")
    cid, created = identifier(), now()
    with connect() as con:
        con.execute("INSERT INTO plan_comparisons VALUES(?,?,?,?,?,?)",(cid,sid,row["revision"],json.dumps(payload,ensure_ascii=False),created,u["username"]))
        audit(con,u["username"],"plans_compared",cid,dict(scenario_id=sid,base_revision=row["revision"],distinct_plans=len(seen)))
        current=con.execute("SELECT revision FROM scenarios WHERE id=?",(sid,)).fetchone()["revision"]
    return present(dict(id=cid,scenario_id=sid,base_revision=row["revision"],data=json.dumps(payload),created=created),current)


@router.get("/scenarios/{sid}/plan-comparisons")
def latest(sid: str, u=Depends(user)):
    require(u,STAFF)
    row,_ = scenario(sid)
    with connect() as con:
        found=con.execute("SELECT * FROM plan_comparisons WHERE scenario_id=? ORDER BY created DESC LIMIT 1",(sid,)).fetchone()
    return present(found,row["revision"]) if found else None


@router.post("/plan-comparisons/{cid}/{key}/select")
def select(cid: str, key: str, u=Depends(user)):
    require(u,{"admin","registrar"})
    if key not in STRATEGIES:
        raise HTTPException(404,"Plan not found")
    with connect() as con:
        con.execute("BEGIN IMMEDIATE")
        row=con.execute("SELECT * FROM plan_comparisons WHERE id=?",(cid,)).fetchone()
        if not row:
            raise HTTPException(404,"Plan comparison not found")
        current=con.execute("SELECT revision,data FROM scenarios WHERE id=?",(row["scenario_id"],)).fetchone()
        if not current or current["revision"]!=row["base_revision"]:
            raise HTTPException(409,"Stale proposal: timetable changed. Compare plans again.")
        payload=json.loads(row["data"])
        plan=next(p for p in payload["plans"] if p["key"]==key)
        if not plan["available"] or not plan["candidate"]:
            raise HTTPException(409,"This plan has no validated improvement. Compare plans again with different limits.")
        # Repeated clicks are idempotent; duplicate strategies share one proposal.
        canonical=next(p for p in payload["plans"] if p["key"]==(plan["same_as"] or key))
        if canonical["proposal_id"]:
            existing=con.execute("SELECT status FROM proposals WHERE id=?",(canonical["proposal_id"],)).fetchone()
            if existing and existing["status"] in {"recommended","approved"}:
                return dict(id=canonical["proposal_id"],status=existing["status"])
        candidate=Semester.model_validate(plan["candidate"])
        issues=validate(candidate)
        if issues:
            raise HTTPException(422,"Hard constraints failed; publication blocked")
        baseline=Semester.model_validate_json(current["data"])
        diff=compare(baseline,candidate)
        after=metrics(candidate,issues)
        summary_keys=["gap_hours","average_days","score","long_gap_2h","worst_decile_gap_hours","load_gini","room_utilization"]
        analysis=dict(comparison=diff,issues=[],conflict_count=0,strategy=key,plan_comparison_id=cid,
                      status=plan["status"],runtime=plan["runtime"],search_scope=plan["search_scope"],
                      before_metrics={k:payload["before"][k] for k in summary_keys},after_metrics={k:after[k] for k in summary_keys})
        pid=identifier()
        con.execute("INSERT INTO proposals VALUES(?,?,?,?,?,?,?,?,?,?)",(pid,row["scenario_id"],row["base_revision"],"optimization","recommended",candidate.model_dump_json(),json.dumps(analysis,ensure_ascii=False),now(),u["username"],f"Selected {key} from compared plans"))
        canonical["proposal_id"]=pid
        for sibling in payload["plans"]:
            if sibling["key"]==canonical["key"] or sibling["same_as"]==canonical["key"]:
                sibling["proposal_id"]=pid
        con.execute("UPDATE plan_comparisons SET data=? WHERE id=?",(json.dumps(payload,ensure_ascii=False),cid))
        audit(con,u["username"],"proposal_created",pid,dict(kind="optimization",status="recommended",scenario_id=row["scenario_id"],strategy=key,plan_comparison_id=cid))
    return dict(id=pid,status="recommended")
