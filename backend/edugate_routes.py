"""Edugate exchange routes: read (no writes) -> user reviews rows -> import into an Edugate timetable; export a PDF."""
import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response
from pydantic import Field
from .models import StrictModel, Semester, Course, Section, Room, Professor, Student, Window, Policy
from .main import user, require, scenario, STAFF
from .analysis import validate
from .store import connect, identifier, now, audit
from . import edugate

router = APIRouter(prefix="/api/edugate")
IMPORTERS = {"admin", "registrar"}
GRID = [480, 570, 660, 800, 890, 980, 1070, 1160]  # 80-minute classes on a 90-minute rhythm, as on the imported schedules
DEFAULT_CAPACITY = 40


@router.post("/read")
async def read(file: UploadFile = File(...), u=Depends(user)):
    require(u, IMPORTERS)
    raw = await file.read()
    try:
        from starlette.concurrency import run_in_threadpool
        result = await run_in_threadpool(edugate.read_schedule, raw, file.filename or "")
    except edugate.ReadError as e:
        raise HTTPException(422, dict(en=e.en, ar=e.ar))
    with connect() as con:
        audit(con, u["username"], "edugate_read", result["format"], {"rows": len(result["rows"])})
    return result


class ImportRow(StrictModel):
    code: str = Field(min_length=2, max_length=20)
    code_ar: str | None = None
    name: str = Field(default="", max_length=200)
    name_ar: str = Field(default="", max_length=200)
    section: str = Field(default="", max_length=20)
    activity: str = Field(default="", max_length=30)
    credits: int | None = Field(default=None, ge=0, le=12)
    days: list[int] = Field(min_length=1, max_length=5)
    start: int = Field(ge=0, lt=1440)
    end: int = Field(gt=0, le=1440)
    room: str = Field(default="", max_length=30)
    warnings: list[dict] = []


class ImportBody(StrictModel):
    student_id: str = Field(min_length=1, max_length=20, pattern=r"^[A-Za-z0-9-]+$")
    student_name: str = Field(min_length=1, max_length=120)
    term: str | None = Field(default=None, max_length=30)
    scenario_id: str | None = None
    name: str | None = Field(default=None, max_length=120)
    rows: list[ImportRow] = Field(min_length=1, max_length=20)


def _pseudonym(student_id):
    """Audit rows identify a student by a short one-way hash, never the university ID."""
    import hashlib
    return "student#" + hashlib.sha256(student_id.encode()).hexdigest()[:10]


def _rooms_window(open_minute, close_minute):
    return [Window(day=d, start=open_minute, end=close_minute) for d in range(5)]


def build(body: ImportBody, base: Semester | None):
    """Merge one reviewed student schedule into an Edugate timetable. Shared sections (same course + section number)
    are reused, so several students' imports describe one timetable. Returns (semester, notes)."""
    notes = []
    by_course = {}
    for i, r in enumerate(body.rows, 1):
        if r.end <= r.start or not 30 <= r.end - r.start <= 240:
            raise HTTPException(422, f"Row {i} ({r.code}): end must be 30–240 minutes after start")
        if any(not 0 <= d <= 4 for d in r.days) or len(set(r.days)) != len(r.days):
            raise HTTPException(422, f"Row {i} ({r.code}): choose distinct days between Sunday and Thursday")
        cid = r.code.replace(" ", "").upper()
        group = by_course.setdefault(cid, dict(row=r, meetings=[]))
        if group["row"].section != r.section:
            raise HTTPException(422, f"{r.code}: a student can only be in one section of a course")
        group["meetings"] += [Window(day=d, start=r.start, end=r.end) for d in r.days]
    for cid, g in by_course.items():
        if len({m.end - m.start for m in g["meetings"]}) > 1:
            raise HTTPException(422, f"{g['row'].code}: every meeting of a course must have the same length in Mizan")
        if len({m.day for m in g["meetings"]}) != len(g["meetings"]):
            raise HTTPException(422, f"{g['row'].code}: two meetings on the same day")
    data = base.model_copy(deep=True) if base else None
    starts = sorted({m.start for g in by_course.values() for m in g["meetings"]})
    ends = [m.end for g in by_course.values() for m in g["meetings"]]
    open_minute = min([480] + [s // 60 * 60 for s in starts] + ([data.policy.open_minute] if data else []))
    close_minute = max([1260] + [-(-e // 60) * 60 for e in ends] + ([data.policy.close_minute] if data else []))
    if data is None:
        policy = Policy(open_minute=open_minute, close_minute=close_minute,
                        allowed_starts=sorted({s for s in GRID + starts if open_minute <= s < close_minute}))
        data = Semester(name=body.name or f"Edugate import · {body.term or datetime.now().strftime('%d/%m/%Y')}", kind="edugate",
                        provenance="Imported from Al Yamamah student schedules (Edugate PDF / app screenshot) by local OCR and reviewed "
                                   "before import. Instructors, room capacities and other room bookings are not in the source: "
                                   f"placeholders are used (one instructor per section, rooms seat {DEFAULT_CAPACITY}).",
                        courses=[], students=[], professors=[], rooms=[], sections=[], policy=policy, term=body.term)
    else:
        data.policy = data.policy.model_copy(update=dict(
            open_minute=open_minute, close_minute=close_minute,
            allowed_starts=sorted({s for s in data.policy.allowed_starts + starts if open_minute <= s < close_minute})))
        data.term = data.term or body.term
    window = _rooms_window(data.policy.open_minute, data.policy.close_minute)
    for res in [*data.rooms, *data.professors]:
        res.availability = window
    courses, rooms = {c.id: c for c in data.courses}, {r.id: r for r in data.rooms}
    sections, professors = {s.id: s for s in data.sections}, {p.id: p for p in data.professors}
    chosen = []
    for cid, g in by_course.items():
        r = g["row"]
        prefix = r.code.split(" ")[0].upper()
        department = edugate.DEPARTMENTS.get(prefix, prefix)
        meetings = sorted(g["meetings"], key=lambda m: m.day)
        if cid not in courses:
            courses[cid] = Course(id=cid, name=r.name or r.code, name_ar=r.name_ar or r.name or r.code, department=department,
                                  competency=department.lower(), duration=meetings[0].end - meetings[0].start,
                                  meetings_per_week=len(meetings), code=r.code, code_ar=r.code_ar, credits=r.credits)
        elif courses[cid].duration != meetings[0].end - meetings[0].start or courses[cid].meetings_per_week != len(meetings):
            notes.append(f"{r.code}: already in this timetable with a different meeting pattern; the existing course was kept.")
        room_id = (r.room or "TBA").upper()
        rooms.setdefault(room_id, Room(id=room_id, name=room_id, capacity=DEFAULT_CAPACITY, availability=window))
        sid = f"{cid}-{r.section or '1'}"
        if sid in sections:
            existing = sections[sid]
            if sorted((m.day, m.start, m.end) for m in existing.meetings) != [(m.day, m.start, m.end) for m in meetings] or existing.room_id != room_id:
                notes.append(f"{r.code} section {r.section or '1'}: already in this timetable at another time or room; the existing section was kept.")
        else:
            pid = f"INS-{sid}"
            professors[pid] = Professor(id=pid, name=f"Instructor · {r.code}" + (f" ({r.section})" if r.section else ""),
                                        department=department, competencies=[courses[cid].competency], contracted_minutes=2400,
                                        availability=window)
            sections[sid] = Section(id=sid, course_id=cid, professor_id=pid, room_id=room_id, capacity=DEFAULT_CAPACITY,
                                    meetings=meetings, label=r.section or None, activity=r.activity or None)
        chosen.append(sid)
    students = [s for s in data.students if s.id != body.student_id]
    students.append(Student(id=body.student_id, name=body.student_name, cohort=body.term or "Edugate import", sections=chosen))
    roster = {}
    for s in students:
        for sid in s.sections:
            roster[sid] = roster.get(sid, 0) + 1
    verified_rooms = set(data.verified.get("rooms", []))
    for sid, section in sections.items():
        enrolled = roster.get(sid, 0)
        room = rooms[section.room_id]
        if enrolled > section.capacity and section.room_id not in verified_rooms:
            notes.append(f"{sid}: {enrolled} imported students exceed the assumed {section.capacity} seats; seats raised to {enrolled} until real capacities are verified.")
            section.capacity = enrolled
        if section.capacity > room.capacity and section.room_id not in verified_rooms:
            notes.append(f"Room {room.id}: assumed capacity raised from {room.capacity} to {section.capacity} for {sid}.")
            room.capacity = section.capacity
    try:
        semester = Semester.model_validate(data.model_copy(update=dict(
            courses=list(courses.values()), rooms=list(rooms.values()), professors=list(professors.values()),
            sections=list(sections.values()), students=students)).model_dump())
    except ValueError as e:
        raise HTTPException(422, f"The schedule cannot be imported: {e}")
    return semester, notes


@router.post("/import")
def import_schedule(body: ImportBody, u=Depends(user)):
    require(u, IMPORTERS)
    if body.scenario_id:
        row, base = scenario(body.scenario_id)
        if base.kind != "edugate":
            raise HTTPException(409, "Schedules can only be added to an Edugate timetable, not to a demo semester")
    else:
        row, base = None, None
    data, notes = build(body, base)
    payload = data.model_dump_json()
    with connect() as con:
        if row is None:
            sid, revision = identifier(), 1
            con.execute("INSERT INTO scenarios VALUES(?,?,?,?)", (sid, data.name, 1, payload))
        else:
            sid, revision = body.scenario_id, row["revision"] + 1
            con.execute("UPDATE scenarios SET revision=?,data=? WHERE id=?", (revision, payload, sid))
        con.execute("INSERT INTO versions VALUES(?,?,?,?)", (sid, revision, payload, now()))
        audit(con, u["username"], "edugate_import", sid, {"scenario_id": sid, "student": _pseudonym(body.student_id), "rows": len(body.rows), "revision": revision})
    return dict(id=sid, revision=revision, name=data.name, students=len(data.students), sections=len(data.sections),
                notes=notes, issues=validate(data)[:50])


def _first_version_with(sid, student_id):
    with connect() as con:
        for v in con.execute("SELECT data FROM versions WHERE scenario_id=? ORDER BY revision", (sid,)):
            data = Semester.model_validate_json(v["data"])
            if any(s.id == student_id for s in data.students):
                return data
    return None


@router.get("/export")
def export(scenario_id: str, student_id: str, proposal_id: str | None = None, u=Depends(user)):
    if u["role"] == "student":
        if student_id != u.get("student_id") or proposal_id:
            raise HTTPException(403, "Students can export only their own published timetable")
    else:
        require(u, STAFF)
    row, data = scenario(scenario_id)
    status_ar, source = "الجدول المعتمد الحالي", f"{data.name} · الإصدار {row['revision']}"
    if proposal_id:
        with connect() as con:
            p = con.execute("SELECT * FROM proposals WHERE id=? AND scenario_id=?", (proposal_id, scenario_id)).fetchone()
        if not p:
            raise HTTPException(404, "Proposal not found")
        data = Semester.model_validate_json(p["data"])
        status_ar = {"recommended": "مقترح بانتظار المراجعة", "approved": "مقترح معتمد بانتظار النشر",
                     "published": "منشور", "rejected": "مقترح مرفوض", "invalid": "مقترح غير صالح"}.get(p["status"], p["status"])
        source = f"مقترح ميزان {proposal_id[:6]} · {data.name}"
    original = _first_version_with(scenario_id, student_id) if data.kind == "edugate" else (scenario(scenario_id)[1] if proposal_id else None)
    try:
        pdf = edugate.render_schedule_pdf(data, student_id, original, status_ar=status_ar, source=source)
    except KeyError:
        raise HTTPException(404, "Student not in this timetable")
    with connect() as con:
        audit(con, u["username"], "edugate_export", scenario_id, {"scenario_id": scenario_id, "student": _pseudonym(student_id), "proposal": proposal_id})
    name = f"schedule-{student_id}" + (f"-proposal-{proposal_id[:6]}" if proposal_id else "") + ".pdf"
    return Response(pdf, media_type="application/pdf", headers={"Content-Disposition": f'inline; filename="{name}"'})


@router.get("/timetables")
def timetables(u=Depends(user)):
    require(u, IMPORTERS)
    with connect() as con:
        rows = con.execute("SELECT id,name,revision,data FROM scenarios ORDER BY rowid").fetchall()
    result = []
    for r in rows:
        data = json.loads(r["data"])
        if data.get("kind") == "edugate":
            result.append(dict(id=r["id"], name=r["name"], revision=r["revision"], students=len(data["students"])))
    return result


def readiness_of(data: Semester):
    """What an imported timetable knows for certain, what it assumes, and what it cannot see (UX review: data readiness)."""
    verified_rooms, verified_sections = set(data.verified.get("rooms", [])), set(data.verified.get("instructors", []))
    used_rooms = {s.room_id for s in data.sections}
    rooms_assumed = sorted(r for r in used_rooms if r not in verified_rooms)
    sections_assumed = sorted(s.id for s in data.sections if s.id not in verified_sections)
    return dict(students=len(data.students), sections=len(data.sections),
                verified=dict(student_conflicts=len(data.students), rooms=len(used_rooms) - len(rooms_assumed), instructors=len(data.sections) - len(sections_assumed)),
                assumed=dict(rooms=rooms_assumed, instructors=sections_assumed, availability=True),
                missing=dict(other_bookings=True, other_students=True),
                ready_to_publish=not rooms_assumed and not sections_assumed)


@router.get("/{sid}/readiness")
def readiness(sid: str, u=Depends(user)):
    require(u, STAFF)
    _, data = scenario(sid)
    if data.kind != "edugate":
        raise HTTPException(404, "Only imported timetables have a readiness report")
    return readiness_of(data)


class RoomFact(StrictModel):
    id: str = Field(min_length=1, max_length=30)
    capacity: int = Field(gt=0, le=2000)


class InstructorFact(StrictModel):
    section_id: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=2, max_length=120)


class VerifyBody(StrictModel):
    rooms: list[RoomFact] = Field(default=[], max_length=500)
    instructors: list[InstructorFact] = Field(default=[], max_length=500)


@router.post("/{sid}/verify")
def verify(sid: str, body: VerifyBody, u=Depends(user)):
    """Record real room capacities and instructors for an imported timetable (a new version; earlier proposals become outdated)."""
    require(u, IMPORTERS)
    row, data = scenario(sid)
    if data.kind != "edugate":
        raise HTTPException(409, "Only imported timetables can be verified here")
    rooms, sections = {r.id: r for r in data.rooms}, {s.id: s for s in data.sections}
    unknown = [r.id for r in body.rooms if r.id.upper() not in rooms] + [i.section_id for i in body.instructors if i.section_id not in sections]
    if unknown:
        raise HTTPException(422, f"Not in this timetable: {', '.join(unknown[:10])}")
    verified = {k: set(v) for k, v in data.verified.items()}
    for fact in body.rooms:
        rooms[fact.id.upper()].capacity = fact.capacity
        verified.setdefault("rooms", set()).add(fact.id.upper())
    professors = {p.id: p for p in data.professors}
    for fact in body.instructors:
        professors[sections[fact.section_id].professor_id].name = fact.name.strip()
        verified.setdefault("instructors", set()).add(fact.section_id)
    data.verified = {k: sorted(v) for k, v in verified.items()}
    data = Semester.model_validate(data.model_dump())
    payload, revision = data.model_dump_json(), row["revision"] + 1
    with connect() as con:
        con.execute("UPDATE scenarios SET revision=?,data=? WHERE id=?", (revision, payload, sid))
        con.execute("INSERT INTO versions VALUES(?,?,?,?)", (sid, revision, payload, now()))
        audit(con, u["username"], "edugate_verify", sid, {"scenario_id": sid, "rooms": len(body.rooms), "instructors": len(body.instructors), "revision": revision})
    return dict(revision=revision, issues=validate(data)[:50], **readiness_of(data))
