"""Regression tests for the 2026-10-05 audit: break rules bind only what a request can move, already-met rules change
nothing, the worse-off limit reaches the solver, whole-word criteria filter, Edugate writes refuse a changed timetable,
and a common free slot seats every distinct student."""
import json
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from backend.analysis import validate, compare
from backend.fixtures import generate
from backend.main import app, scenario, USERS
from backend import agent_engine as ae, edugate_routes
from backend.models import Semester
from backend.recruitment import validate_criteria, JobInput
from backend.rules import RuleSet, BreakRule, TimeRule, optimize_with_rules, check_rules
from backend.solver import optimize, common_slots
from backend.store import connect, init_db, identifier, now
from test_finder import tiny

HOURS = [{"day": d, "start": 480, "end": 720} for d in range(5)]


def week(student_sections):
    """08:00-12:00, one meeting per course. S1 (P1, the request's scope) Mon 10-11. P2 teaches S2 Sun 8-9, S3 Sun 9-10
    (back to back, outside the scope) and S4 Mon 11-12 (right after S1)."""
    course = lambda i: dict(id=f"C{i}", name=f"Course {i}", name_ar=f"مقرر {i}", department="Computing", competency="computing", meetings_per_week=1)
    section = lambda i, prof, room, day, h: dict(id=f"S{i}", course_id=f"C{i}", professor_id=prof, room_id=room, capacity=10,
                                                 meetings=[dict(day=day, start=h * 60, end=h * 60 + 60)])
    return Semester(name="week", provenance="test", courses=[course(i) for i in range(1, 5)],
                    professors=[dict(id=p, name=p, department="Computing", competencies=["computing"], contracted_minutes=600, availability=HOURS) for p in ["P1", "P2"]],
                    rooms=[dict(id=r, name=r, capacity=10, availability=HOURS) for r in ["R1", "R2"]],
                    sections=[section(1, "P1", "R1", 1, 10), section(2, "P2", "R2", 0, 8), section(3, "P2", "R2", 0, 9), section(4, "P2", "R2", 1, 11)],
                    students=[dict(id="X", name="X", cohort="c", sections=student_sections)])


def student_break(minutes=10):
    return RuleSet(scope_sections=["S1"], max_changes=1, breaks=[BreakRule(minutes=minutes, kind="between_each", applies_to="students")])


# ---------- 1. break rules bind only pairs the request can move ----------

def test_short_break_between_two_fixed_sections_does_not_block_a_student_break_rule():
    data = week(["S1", "S2", "S3"])  # only S2-S3 (both outside the scope) are back to back
    assert check_rules(data, data, student_break()) == []
    result = optimize_with_rules(data, student_break(), seconds=5)
    assert result["status"] != "INFEASIBLE" and not result["comparison"]["changes"]


def test_student_break_moves_the_scoped_section_and_leaves_fixed_pairs_alone():
    data = week(["S1", "S2", "S3", "S4"])  # S1 ends where S4 starts: the request's own short break
    assert [v["rule"] for v in check_rules(data, data, student_break())] == ["break:0"]
    result = optimize_with_rules(data, student_break(), seconds=5)
    assert result["status"] in {"OPTIMAL", "FEASIBLE"}, result.get("diagnosis")
    candidate = Semester.model_validate(result["candidate"])
    after = {s.id: s for s in candidate.sections}
    before = {s.id: s for s in data.sections}
    assert after["S1"] != before["S1"] and all(after[s] == before[s] for s in ["S2", "S3", "S4"])
    assert validate(candidate) == [] and check_rules(data, candidate, student_break()) == []


def test_one_free_block_rule_ignores_a_day_with_no_section_in_scope():
    # P2's Sunday (S2, S3 back to back) is entirely outside the scope; the rule concerns S4's Monday only.
    data = week(["S1", "S2", "S3", "S4"])
    rules = RuleSet(scope_sections=["S4"], max_changes=1, professors=["P2"],
                    breaks=[BreakRule(minutes=60, kind="one_block", applies_to="professor")])
    assert check_rules(data, data, rules) == []
    assert optimize_with_rules(data, rules, seconds=5)["status"] != "INFEASIBLE"


def test_faculty_student_break_no_longer_fails_on_other_professors_classes():
    data = generate("faculty")
    own = [s.id for s in data.sections if s.professor_id == "P001"]
    rules = RuleSet(scope_sections=own, max_changes=5, breaks=[BreakRule(minutes=10, kind="between_each", applies_to="students")])
    # Every remaining violation on the official timetable now involves one of the professor's own sections.
    for violation in check_rules(data, data, rules):
        key = violation["detail"].split(":")[0].removeprefix("students ").split("|")
        assert set(key) & set(own)
    result = optimize_with_rules(data, rules, seconds=10)
    if result.get("candidate"):
        assert check_rules(data, Semester.model_validate(result["candidate"]), rules) == []


# ---------- 2. an already-met rule request changes nothing ----------

def test_rule_request_already_met_returns_no_change():
    data = generate("faculty")
    own = [s.id for s in data.sections if s.professor_id == "P001"]
    result = optimize_with_rules(data, RuleSet(scope_sections=own, max_changes=5, windows=[TimeRule(earliest_start=480)]), seconds=5)
    assert result["status"] == "OPTIMAL" and result["already_satisfied"]
    assert result["comparison"]["changes"] == [] and "candidate" not in result


def test_explicit_move_request_still_runs_when_other_rules_are_met():
    data = generate("faculty")
    own = [s.id for s in data.sections if s.professor_id == "P001"]
    result = optimize_with_rules(data, RuleSet(scope_sections=own, max_changes=1, must_change=[own[0]]), seconds=10)
    # The solver ran (in faculty week S087 may genuinely have no clash-free slot); it never short-cut to "already met".
    assert not result.get("already_satisfied") and result["status"] in {"OPTIMAL", "FEASIBLE", "INFEASIBLE"}
    if result.get("comparison"):
        assert {c["section_id"] for c in result["comparison"]["changes"]} == {own[0]}


# ---------- 3. the worse-off limit is a solver constraint ----------

def test_worse_off_limit_in_the_full_model():
    data = generate("faculty")
    own = {s.id for s in data.sections if s.professor_id == "P001"}
    free = optimize(data, 5, 10, movable=own)
    assert free["comparison"]["worsened"] > 0  # without a limit the best own-section move harms a few students
    capped = optimize(data, 5, 10, movable=own, max_worsened=0)
    assert capped["status"] == "OPTIMAL" and capped["max_worsened"] == 0
    assert capped["comparison"]["worsened"] == 0


def test_worse_off_limit_in_the_large_neighbourhood_search():
    data = generate("faculty")
    result = optimize(data, 5, 8, max_worsened=0)
    assert result["status"] == "FEASIBLE" and result["max_worsened"] == 0
    diff = compare(data, Semester.model_validate(result["candidate"]))
    assert diff["worsened"] == 0 and diff["changes"] and diff["recovered_hours"] > 0


def test_agent_scheduling_honours_max_worsened(tmp_path, monkeypatch):
    """Faculty week: every unconstrained plan harms students, so impact review used to reject every revision."""
    monkeypatch.setenv("MIZAN_DB", str(tmp_path / "agents.sqlite3"))
    init_db(); ae.init_agents()
    monkeypatch.setattr(ae.local_model, "status", lambda: {"available": True, "coordinator_model": "test"})
    row, data = scenario("faculty")
    limits = {"max_changes": 5, "max_worsened": 0, "solver_seconds": 6}
    rid = identifier()
    with connect() as con:
        con.execute("INSERT INTO agent_runs VALUES(?,?,?,?,?,?,?,?,?,?,?)", (rid, "faculty", 1, "test", json.dumps(limits), "queued", None, now(), now(), "admin", 0))
    def scripted(role, ctx, actions):
        if role == "coordinator":
            pending = ctx["pending_specialists"]
            return ae.Decision(action="delegate" if pending else "finalize", agent=pending[0] if pending else "student"), {}
        if "report" in actions and role in ctx["evidence"]:
            return ae.Decision(action="report"), {}
        return ae.Decision(action=next(a for a in actions if a != "report"), max_changes=5), {}
    monkeypatch.setattr(ae, "model_decision", scripted)
    ae.run_collaboration(rid, "faculty", row, data, "Reduce gaps without harming anyone", limits, dict(username="admin", **USERS["admin"]))
    with connect() as con:
        run = con.execute("SELECT * FROM agent_runs WHERE id=?", (rid,)).fetchone()
        result = json.loads(run["result"])
        assert run["status"] == "completed" and result["disposition"] == "recommend", result
        proposal = json.loads(con.execute("SELECT analysis FROM proposals WHERE id=?", (result["proposal_id"],)).fetchone()[0])
    assert proposal["comparison"]["worsened"] == 0 and proposal["comparison"]["changes"]


# ---------- 4. hiring criteria: whole words only ----------

@pytest.mark.parametrize("text,allowed", [
    ("Embraces peer review in teaching", True), ("Experience with distributed tracing", True), ("Graduate teaching experience", True),
    ("Candidate race", False), ("Racial background", False), ("Religious affiliation", False), ("Nationality: Saudi", False),
    ("Pregnancy status", False), ("Age limit of 40", False), ("Gender", False), ("الجنسية سعودية", False)])
def test_criteria_filter_matches_whole_words(text, allowed):
    body = JobInput(title="Lecturer", criteria=[dict(id="a", category="teaching", description=text, weight=10)])
    if allowed:
        validate_criteria(body)
    else:
        with pytest.raises(HTTPException):
            validate_criteria(body)


# ---------- 5. Edugate writes refuse a timetable that changed meanwhile ----------

ROWS = [dict(code="MKT 201", section="12", days=[0, 2], start=480, end=560, room="B-12")]


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("MIZAN_DB", str(tmp_path / "edugate.sqlite3"))
    monkeypatch.delenv("MIZAN_DEMO_PASSWORD", raising=False)
    with TestClient(app, headers={"X-Mizan-Action": "1"}) as c:
        assert c.post("/api/login", json={"username": "admin", "password": "Mizan-demo-2026!"}).status_code == 200
        yield c


def publish_meanwhile(monkeypatch):
    """The timetable is read, then (before the write) someone else publishes a new revision."""
    real = edugate_routes.scenario
    def stale(sid):
        row, data = real(sid)
        with connect() as con:
            con.execute("UPDATE scenarios SET revision=revision+1 WHERE id=?", (sid,))
        return row, data
    monkeypatch.setattr(edugate_routes, "scenario", stale)


@pytest.mark.parametrize("action", ["verify", "import"])
def test_edugate_write_refuses_a_changed_timetable(client, monkeypatch, action):
    sid = client.post("/api/edugate/import", json=dict(student_id="T1", student_name="A", rows=ROWS)).json()["id"]
    publish_meanwhile(monkeypatch)
    if action == "verify":
        response = client.post(f"/api/edugate/{sid}/verify", json=dict(rooms=[dict(id="B-12", capacity=50)]))
    else:
        response = client.post("/api/edugate/import", json=dict(student_id="T2", student_name="B", rows=ROWS, scenario_id=sid))
    assert response.status_code == 409
    with connect() as con:
        row = con.execute("SELECT revision, data FROM scenarios WHERE id=?", (sid,)).fetchone()
        assert row["revision"] == 2 and con.execute("SELECT max(revision) FROM versions WHERE scenario_id=?", (sid,)).fetchone()[0] == 1
    data = Semester.model_validate_json(row["data"])
    assert [s.id for s in data.students] == ["T1"] and not data.verified  # nothing was overwritten


# ---------- 6. one common session seats every distinct student ----------

def test_common_slot_room_seats_all_students_of_all_sections():
    # S1 (A B C) + S2 (D E): five students together need the hall, not a 4-seat room sized for the larger section.
    result = common_slots(tiny(), ["S1", "S2"], 60, days=[4], limit=5)
    assert result["group_size"] == 5 and result["slots"][0]["rooms"] == ["R3"]
