"""Natural-language requests: interpret -> review/revise -> confirm (spec §18.2). Nothing runs before confirmation."""
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, HTTPException
from pydantic import Field, ValidationError
from .models import StrictModel, Window
from .main import user, require, scenario
from .analysis import validate, compare
from .store import connect, identifier, now, audit
from . import local_model, interpreter as it

router = APIRouter(prefix='/api/requests')
ROLES = {"admin", "registrar", "chair", "professor"}


def init_requests():
    with connect() as con:
        con.execute('''CREATE TABLE IF NOT EXISTS request_interpretations(id TEXT PRIMARY KEY,scenario_id TEXT NOT NULL,revision INTEGER NOT NULL,
            username TEXT NOT NULL,role TEXT NOT NULL,text TEXT NOT NULL,language TEXT NOT NULL,interpretation TEXT NOT NULL,
            status TEXT NOT NULL,version INTEGER NOT NULL,created TEXT NOT NULL,updated TEXT NOT NULL)''')


def context_for(u, data):
    own = [s.id for s in data.sections if u["role"] == "professor" and s.professor_id == u.get("professor_id")]
    return dict(requester_role=u["role"], own_sections=own, today=datetime.now(ZoneInfo(data.policy.timezone)).date().isoformat())


def load(rid, u):
    with connect() as con:
        row = con.execute("SELECT * FROM request_interpretations WHERE id=?", (rid,)).fetchone()
    if not row or row["username"] != u["username"]:
        raise HTTPException(404, "Request not found")
    return dict(row)


def present(row, interp, resolution):
    return dict(id=row["id"], scenario_id=row["scenario_id"], revision=row["revision"], text=row["text"], language=row["language"],
                status=row["status"], version=row["version"], interpretation=interp.model_dump(), resolution=resolution,
                next_step=it.next_step(interp), date_note=dict(en=it.DATE_NOTE[0], ar=it.DATE_NOTE[1]) if interp.date_note else None)


class InterpretBody(StrictModel):
    scenario_id: str
    text: str = Field(min_length=3, max_length=1500)


@router.post('/interpret')
def interpret(body: InterpretBody, u=Depends(user)):
    require(u, ROLES)
    row, data = scenario(body.scenario_id)
    if not local_model.status()['available']:
        raise HTTPException(503, "Start the local model service to interpret requests")
    try:
        interp, telemetry = it.interpret(body.text, context_for(u, data))
    except (ValidationError, ValueError) as error:
        raise HTTPException(422, f"The request could not be interpreted reliably: {str(error)[:200]}")
    resolution = it.resolve(interp, data, u)
    rid = identifier()
    record = dict(id=rid, scenario_id=body.scenario_id, revision=row["revision"], text=body.text, language=it.language(body.text),
                  status="draft", version=1)
    with connect() as con:
        con.execute("INSERT INTO request_interpretations VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                    (rid, body.scenario_id, row["revision"], u["username"], u["role"], body.text, record["language"], it.dumps(interp), "draft", 1, now(), now()))
        audit(con, u["username"], "request_interpreted", rid, dict(scenario_id=body.scenario_id, task=interp.task, telemetry=telemetry,
                                                                   unsupported=[x["code"] for x in interp.unsupported]))
    return present(record, interp, resolution)


class ReviseBody(StrictModel):
    interpretation: dict


@router.post('/{rid}/revise')
def revise(rid: str, body: ReviseBody, u=Depends(user)):
    """The user corrects fields. Code re-derives support, questions and resolution; client-sent verdicts are ignored."""
    require(u, ROLES)
    row = load(rid, u)
    if row["status"] != "draft":
        raise HTTPException(409, "Only draft requests can be corrected")
    fields = {k: v for k, v in body.interpretation.items() if k in it.Extracted.model_fields}
    current = json.loads(row["interpretation"])
    raw = {**{k: current[k] for k in it.Extracted.model_fields}, **fields}
    _, data = scenario(row["scenario_id"])
    try:
        # Support, questions and date handling are re-derived by code from the corrected fields and the original text.
        interp = it.postprocess(raw, context_for(u, data), it.normalize_text(row["text"]))
    except (ValidationError, ValueError) as error:
        raise HTTPException(422, f"Invalid correction: {str(error)[:300]}")
    with connect() as con:
        con.execute("UPDATE request_interpretations SET interpretation=?,version=version+1,updated=? WHERE id=?", (it.dumps(interp), now(), rid))
        audit(con, u["username"], "request_revised", rid, dict(version=row["version"] + 1))
    row.update(version=row["version"] + 1)
    return present(row, interp, it.resolve(interp, data, u))


@router.post('/{rid}/confirm')
def confirm(rid: str, u=Depends(user)):
    """Confirm the stored interpretation. Only fully specified single-meeting moves run now (a read-only preview)."""
    require(u, ROLES)
    row = load(rid, u)
    if row["status"] != "draft":
        raise HTTPException(409, "This request was already confirmed or cancelled")
    current_row, data = scenario(row["scenario_id"])
    interp = it.Interpretation.model_validate_json(row["interpretation"])
    resolution = it.resolve(interp, data, u)
    if resolution["blocked"]:
        raise HTTPException(409, "Resolve the listed issues before confirming")
    if interp.needs_clarification or resolution["questions"]:
        raise HTTPException(409, "Answer the open questions before confirming")
    if interp.unsupported and it.next_step(interp) == "none":
        raise HTTPException(409, "Nothing in this request is supported yet")
    result = dict(step=it.next_step(interp), previews=[])
    if result["step"] == "preview_move" and u["role"] in {"admin", "registrar", "professor"}:
        for meeting in resolution["meetings"][:1]:
            target = it.move_target(interp, meeting)
            if target:
                result["previews"].append(preview(data, current_row, meeting, target))
    with connect() as con:
        con.execute("UPDATE request_interpretations SET status='confirmed',revision=?,updated=? WHERE id=?", (current_row["revision"], now(), rid))
        audit(con, u["username"], "request_confirmed", rid, dict(version=row["version"], step=result["step"], revision=current_row["revision"]))
    row.update(status="confirmed", revision=current_row["revision"])
    from .main import redact
    return dict(**present(row, interp, resolution), result=redact(u, result))


def preview(data, row, meeting, target):
    """Same read-only check as POST /preview-change; nothing is saved."""
    from .main import baseline_issue_keys
    candidate = data.model_copy(deep=True)
    section = next(s for s in candidate.sections if s.id == meeting["section_id"])
    duration = meeting["end"] - meeting["start"]
    if target["start"] < 0 or target["start"] + duration > 1440:
        return dict(**meeting, target=target, feasible=False, new_issue_count=0, error="Meeting would extend past midnight")
    section.meetings[meeting["meeting_index"]] = Window(day=target["day"], start=target["start"], end=target["start"] + duration)
    existing = baseline_issue_keys(row["id"], row, data)
    introduced = [i for i in validate(candidate) if (i["code"], tuple(i["records"])) not in existing]
    diff = compare(data, candidate)
    return dict(**meeting, target=dict(**target, end=target["start"] + duration), feasible=not introduced, new_issues=introduced[:20],
                new_issue_count=len(introduced), recovered_hours=diff["recovered_hours"], worsened=diff["worsened"])


@router.post('/{rid}/cancel')
def cancel(rid: str, u=Depends(user)):
    require(u, ROLES)
    row = load(rid, u)
    if row["status"] != "draft":
        raise HTTPException(409, "Only draft requests can be cancelled")
    with connect() as con:
        con.execute("UPDATE request_interpretations SET status='cancelled',updated=? WHERE id=?", (now(), rid))
        audit(con, u["username"], "request_cancelled", rid, {})
    return {"status": "cancelled"}


@router.get('')
def mine(scenario_id: str, u=Depends(user)):
    require(u, ROLES)
    with connect() as con:
        rows = con.execute("SELECT id,text,language,status,version,created,interpretation FROM request_interpretations WHERE username=? AND scenario_id=? ORDER BY created DESC LIMIT 20",
                           (u["username"], scenario_id)).fetchall()
    return [dict(id=r["id"], text=r["text"], language=r["language"], status=r["status"], version=r["version"], created=r["created"],
                 task=json.loads(r["interpretation"])["task"]) for r in rows]
