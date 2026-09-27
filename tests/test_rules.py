"""Scheduling rules (spec §18.4): one solver test per rule, the independent checker, diagnosis and the request path."""
import json
import re
import pytest
from fastapi.testclient import TestClient
from backend import local_model
from backend.fixtures import generate
from backend.models import Semester, Window
from backend.analysis import validate
from backend.rules import (RuleSet, TimeRule, BreakRule, DayMove, ProtectRule, optimize_with_rules, check_rules, option_ok, rule_items, without)
from backend.main import app
from backend.store import connect


@pytest.fixture(scope="module")
def faculty():
    return generate("faculty")


@pytest.fixture(scope="module")
def own(faculty):
    return [s.id for s in faculty.sections if s.professor_id == "P001"]


def run(data, rules):
    result = optimize_with_rules(data, rules, seconds=10)
    if result.get("candidate"):
        candidate = Semester.model_validate(result["candidate"])
        assert validate(candidate) == []
        assert check_rules(data, candidate, rules) == []  # independent check agrees with the solver
        result["after"] = {s.id: s for s in candidate.sections}
    return result


def changed(result):
    return {c["section_id"] for c in result.get("comparison", {}).get("changes", [])}


def test_time_window_moves_only_what_breaks_it(faculty, own):
    rules = RuleSet(scope_sections=own, professors=["P001"], max_changes=5, windows=[TimeRule(earliest_start=540)])
    r = run(faculty, rules)
    assert r["status"] == "OPTIMAL" and changed(r) == {"S091"}  # the only 08:00 class
    assert all(m.start >= 540 for sid in own for m in r["after"][sid].meetings)
    before = {s.id: s for s in faculty.sections}
    assert all(r["after"][s.id] == before[s.id] for s in faculty.sections if s.id not in own)


def test_split_times_only_when_a_rule_requires_it_and_labelled(faculty, own):
    # Monday stays (protected); Wednesday must start at 14:00 or later: meeting times must differ.
    rules = RuleSet(scope_sections=own, professors=["P001"], max_changes=1,
                    protected=[ProtectRule(section="S091", days=[1])], windows=[TimeRule(earliest_start=840, days=[3])])
    r = run(faculty, rules)
    assert r["status"] == "OPTIMAL" and changed(r) == {"S091"}
    meetings = {m.day: m.start for m in r["after"]["S091"].meetings}
    assert meetings == {1: 480, 3: 840}
    split = r["split_times"][0]
    assert split["section_id"] == "S091" and split["reasons"][0]["en"].startswith("Time window") and split["reasons"][0]["ar"]
    # Without a day-limited rule, sections keep one start time for all meetings.
    plain = run(faculty, RuleSet(scope_sections=own, professors=["P001"], max_changes=5, windows=[TimeRule(earliest_start=540)]))
    assert plain["split_times"] == []


def test_protected_sections_and_locked_days_are_exempt_and_unchanged(faculty, own):
    for rules in [RuleSet(scope_sections=own, max_changes=5, protected=[ProtectRule(section="S091")], windows=[TimeRule(earliest_start=540)]),
                  RuleSet(scope_sections=own, max_changes=5, locked_days=[1, 3], windows=[TimeRule(earliest_start=540)])]:
        r = run(faculty, rules)
        assert r["status"] == "OPTIMAL" and "S091" not in changed(r)


def test_professor_breaks_between_classes_and_one_free_block(faculty, own):
    between = run(faculty, RuleSet(scope_sections=own, professors=["P001"], max_changes=2,
                                   breaks=[BreakRule(minutes=30, days=[4], kind="between_each", applies_to="professor")]))
    assert between["status"] == "OPTIMAL" and changed(between)
    thursday = sorted((m for s in between["after"].values() if s.professor_id == "P001" for m in s.meetings if m.day == 4), key=lambda m: m.start)
    assert all(b.start - a.end >= 30 for a, b in zip(thursday, thursday[1:]))
    block = run(faculty, RuleSet(scope_sections=own, professors=["P001"], max_changes=2,
                                 breaks=[BreakRule(minutes=120, days=[4], kind="one_block", applies_to="professor")]))
    assert block["status"] == "OPTIMAL" and len(changed(block)) <= 2
    thursday = sorted((m for s in block["after"].values() if s.professor_id == "P001" for m in s.meetings if m.day == 4), key=lambda m: m.start)
    assert len(thursday) <= 1 or max(b.start - a.end for a, b in zip(thursday, thursday[1:])) >= 120


def test_day_to_empty_keep_time():
    baseline = generate("baseline")
    r = run(baseline, RuleSet(scope_sections=["S001"], max_changes=1, keep_time=True, day_to_empty=DayMove(from_day=2, to_day=3)))
    assert r["status"] == "OPTIMAL"
    assert [(m.day, m.start) for m in r["after"]["S001"].meetings] == [(1, 480), (3, 480)]


def test_required_room_change_keeps_day_and_time(faculty, own):
    r = run(faculty, RuleSet(scope_sections=own, max_changes=1, keep_days=True, keep_time=True, must_change_room=["S087"]))
    before = next(s for s in faculty.sections if s.id == "S087")
    assert r["status"] == "OPTIMAL" and r["after"]["S087"].room_id != before.room_id
    assert r["after"]["S087"].meetings == before.meetings


def test_infeasible_rules_are_diagnosed_and_timetable_kept(faculty, own):
    # Every Wednesday slot ending by 14:00 clashes with some of S089's students.
    rules = RuleSet(scope_sections=own, max_changes=5, keep_days=True, windows=[TimeRule(latest_end=840, days=[3])])
    r = optimize_with_rules(faculty, rules, seconds=10)
    assert r["status"] == "INFEASIBLE" and "candidate" not in r
    assert [b["id"] for b in r["diagnosis"]["blocking_rules"]] == ["window:0"]
    assert r["diagnosis"]["ar"]
    impossible = optimize_with_rules(faculty, RuleSet(scope_sections=own, max_changes=5, windows=[TimeRule(latest_end=540)]), seconds=5)
    assert impossible["status"] == "INFEASIBLE" and impossible["blocked_section"]


def test_checker_catches_each_violation_independently(faculty, own):
    before = faculty
    after = faculty.model_copy(deep=True)
    sec = {s.id: s for s in after.sections}
    sec["S091"].meetings[0] = Window(day=1, start=420 + 60, end=540)  # unchanged times, placeholder
    sec["S091"].meetings[1] = Window(day=3, start=600, end=660)        # Wednesday moved to 10:00
    sec["S087"].room_id = "R040"
    sec["S001"].meetings[0] = Window(day=0, start=540, end=600)         # outside scope
    rules = RuleSet(scope_sections=own, max_changes=1, keep_time=True, keep_room=True, locked_days=[3],
                    protected=[ProtectRule(section="S087")], windows=[TimeRule(latest_end=630)],
                    breaks=[BreakRule(minutes=400, days=[1], kind="between_each", applies_to="professor")], professors=["P001"],
                    must_change=["S088"], day_to_empty=DayMove(from_day=1, to_day=2))
    found = {v["rule"] for v in check_rules(before, after, rules)}
    assert {"scope", "max_changes", "keep_room", "protected", "locked_days", "window:0", "must_change", "day_to_empty", "break:0"} <= found
    assert check_rules(before, before, RuleSet(scope_sections=own, max_changes=0)) == []


def test_option_filter_and_rule_labels(faculty):
    s = next(x for x in faculty.sections if x.id == "S091")
    moved = s.model_copy(update=dict(meetings=[Window(day=1, start=540, end=600), Window(day=3, start=540, end=600)]))
    assert option_ok(RuleSet(scope_sections=["S091"], max_changes=1, windows=[TimeRule(earliest_start=540)]), s, moved)
    assert not option_ok(RuleSet(scope_sections=["S091"], max_changes=1, keep_time=True), s, moved)
    assert not option_ok(RuleSet(scope_sections=["S091"], max_changes=1, locked_days=[1]), s, moved)
    rules = RuleSet(scope_sections=["S091"], max_changes=2, keep_days=True, windows=[TimeRule(latest_end=840, days=[3])])
    items = rule_items(rules)
    assert [i["id"] for i in items] == ["window:0", "keep_days", "max_changes"] and all(i["ar"] for i in items)
    assert without(rules, "window:0").windows == [] and without(rules, "keep_days").keep_days is False


# ---------- request path: interpret -> confirm -> rules -> proposal ----------

STUDENT_ID = re.compile(r"\bST\d{4}\b")


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("MIZAN_DB", str(tmp_path / "rules.sqlite3"))
    monkeypatch.delenv("MIZAN_DEMO_PASSWORD", raising=False)
    monkeypatch.setattr(local_model, "status", lambda: {"available": True, "coordinator_model": "pretrained"})
    state = {}
    monkeypatch.setattr(local_model, "structured", lambda *a, **k: (json.loads(json.dumps(state["raw"])), {"model": "fake"}))
    with TestClient(app, headers={"X-Mizan-Action": "1"}) as c:
        c.state = state
        yield c


def login(c, name):
    assert c.post('/api/login', json={"username": name, "password": "Mizan-demo-2026!"}).status_code == 200


WINDOW_9 = {"task": "reschedule_with_rules", "scope": "own", "date_scope": {"kind": "weekly", "phrase": ""},
            "allowed_time_window": {"earliest_start": "09:00", "latest_start": None, "latest_end": None, "days": []}}


def test_professor_rule_request_becomes_a_checked_proposal(client):
    login(client, "professor")
    client.state["raw"] = WINDOW_9
    rid = client.post('/api/requests/interpret', json={"scenario_id": "faculty", "text": "خل الكلاسات ما تبدا قبل ٩"}).json()["id"]
    done = client.post(f'/api/requests/{rid}/confirm', json={})
    assert done.status_code == 200, done.text
    result = done.json()["result"]
    assert result["step"] == "optimize_with_rules" and result["status"] == "OPTIMAL"
    assert result["rule_violations"] == [] and result["proposal"]["status"] == "recommended"
    assert not STUDENT_ID.search(json.dumps(done.json()))
    with connect() as db:
        kind, analysis = db.execute("SELECT kind, analysis FROM proposals").fetchone()
        assert kind == "rule_change" and json.loads(analysis)["rule_items"][0]["id"] == "window:0"
        assert db.execute("SELECT revision FROM scenarios WHERE id='faculty'").fetchone()[0] == 1  # nothing published


def test_dated_rule_request_never_runs_as_weekly(client):
    login(client, "professor")
    client.state["raw"] = {**WINDOW_9, "date_scope": {"kind": "date_range", "phrase": "rest of November"}}
    body = client.post('/api/requests/interpret', json={"scenario_id": "faculty", "text": "For the rest of November nothing before 9"}).json()
    assert body["next_step"] == "none"
    assert client.post(f'/api/requests/{body["id"]}/confirm', json={}).status_code == 409
    # An explicit correction to the weekly timetable is the user's decision; then it runs.
    revised = client.post(f'/api/requests/{body["id"]}/revise', json={"interpretation": {"date_scope": {"kind": "weekly", "phrase": ""}}}).json()
    assert revised["interpretation"]["unsupported"][0]["code"] == "DATED_CHANGE"  # the text still names a period
    with connect() as db:
        assert db.execute("SELECT count(*) FROM proposals").fetchone()[0] == 0


def test_chair_sees_rule_results_without_creating_proposals(client):
    login(client, "chair")
    client.state["raw"] = {**WINDOW_9, "scope": "sections", "target_sections": ["S091"]}
    body = client.post('/api/requests/interpret', json={"scenario_id": "faculty", "text": "section 91 not before 9"}).json()
    done = client.post(f'/api/requests/{body["id"]}/confirm', json={}).json()
    assert done["result"]["status"] == "OPTIMAL" and done["result"]["proposal"] is None
    with connect() as db:
        assert db.execute("SELECT count(*) FROM proposals").fetchone()[0] == 0
