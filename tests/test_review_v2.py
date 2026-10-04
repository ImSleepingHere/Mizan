"""Findings of the second expert review (Mizan-Expert-Review-V2.md, 4 Oct 2026), fixed and pinned."""
import json
import re
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.fixtures import generate
from backend.rules import RuleSet, BreakRule, _break_groups, student_groups_in_scope

ROWS = [dict(code="MKT 201", code_ar="تسق 201", section="12", activity="نظري", credits=3, days=[0, 2], start=480, end=560, room="B-12")]


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("MIZAN_DB", str(tmp_path / "v2.sqlite3"))
    monkeypatch.delenv("MIZAN_DEMO_PASSWORD", raising=False)
    with TestClient(app, headers={"X-Mizan-Action": "1"}) as c:
        yield c


def login(c, name):
    assert c.post("/api/login", json={"username": name, "password": "Mizan-demo-2026!"}).status_code == 200


def test_preview_and_proposal_agree_when_conflicts_already_exist(client):
    """COR-1: on a timetable that already has conflicts, a move is not previewed as feasible and then saved as invalid."""
    login(client, "admin")
    data = client.get("/api/scenarios/diagnostic").json()
    s = data["sections"][10]
    m = s["meetings"][0]
    for day in range(5):
        for start in range(480, 1020, 60):
            if (day, start) == (m["day"], m["start"]) or any(x["day"] == day for k, x in enumerate(s["meetings"]) if k):
                continue
            p = client.post("/api/scenarios/diagnostic/preview-change", json=dict(section_id=s["id"], meeting_index=0, day=day, start=start)).json()
            if p["new_issue_count"] == 0:
                assert p["feasible"] is False and p["blocked_by_existing"] is True and p["existing_issue_count"] > 0
                saved = client.post("/api/scenarios/diagnostic/changes", json=dict(section_id=s["id"], meeting_index=0, day=day, start=start, reason="Check")).json()
                assert saved["status"] == "invalid"  # consistent with the preview: not approvable
                return
    pytest.skip("no conflict-free move found for this section")


def test_rule_checker_sees_every_student_pattern():
    """COR-3: the independent checker groups students like the solver (full enrollment pattern), not by first section."""
    data = generate("faculty")
    own = [s.id for s in data.sections if s.professor_id == "P001"]
    rules = RuleSet(scope_sections=own, max_changes=2, breaks=[BreakRule(minutes=30, kind="between_each", applies_to="students")])
    assert len(_break_groups(data, rules, rules.breaks[0])) == len(student_groups_in_scope(data, rules)) > 50


def test_students_at_risk_counts_only_unseated(client):
    """COR-4: 112 students want the course, 2 of 3 sections run, so 36 are without a seat."""
    login(client, "admin")
    signal = client.get("/api/scenarios/shortfall/workforce").json()["signals"][0]
    assert signal["students_demanding"] == 112 and signal["students_at_risk"] == 36


def test_import_reports_raised_capacities_and_never_raises_verified_rooms(client):
    """COR-2: over-capacity imports are reported; a verified room keeps its capacity and shows a capacity issue."""
    login(client, "admin")
    sid = client.post("/api/edugate/import", json=dict(student_id="T0", student_name="A", rows=ROWS)).json()["id"]
    assert client.post(f"/api/edugate/{sid}/verify", json=dict(rooms=[dict(id="B-12", capacity=2)])).status_code == 200
    r = client.post("/api/edugate/import", json=dict(student_id="T1", student_name="B", rows=ROWS, scenario_id=sid)).json()
    assert r["notes"] == [] or all("B-12" not in n for n in r["notes"] if n.startswith("Room"))
    r = client.post("/api/edugate/import", json=dict(student_id="T2", student_name="C", rows=ROWS, scenario_id=sid)).json()
    assert any(i["code"] == "CAPACITY" for i in r["issues"])  # 3 students, verified 2-seat room: reported, not hidden
    other = client.post("/api/edugate/import", json=dict(student_id="U1", student_name="D", rows=[dict(ROWS[0], room="A-09", section="13")])).json()
    assert other["notes"] == []


def test_audit_never_holds_a_raw_student_id(client):
    """SEC-3: import and export audit rows carry a one-way pseudonym, not the university ID."""
    login(client, "admin")
    sid = client.post("/api/edugate/import", json=dict(student_id="202514999", student_name="A", rows=ROWS)).json()["id"]
    assert client.get(f"/api/edugate/export?scenario_id={sid}&student_id=202514999").status_code == 200
    rows = [r for r in client.get("/api/audit").json() if r["action"].startswith("edugate_")]
    assert rows and "202514999" not in json.dumps(rows) and all(r["detail"]["student"].startswith("student#") for r in rows)


def test_shared_password_refused_from_other_computers(client):
    """SEC-1: with the default demo password, sign-in only works from this computer."""
    from backend import main
    r = client.post("/api/login", json={"username": "admin", "password": "Mizan-demo-2026!"})
    assert r.status_code == 200 and "testclient" in main.LOOPBACK
    remote = TestClient(app, headers={"X-Mizan-Action": "1"}, client=("192.168.1.20", 50000))
    blocked = remote.post("/api/login", json={"username": "admin", "password": "Mizan-demo-2026!"})
    assert blocked.status_code == 403 and "MIZAN_DEMO_PASSWORD" in blocked.json()["detail"]


def test_professor_responses_never_contain_student_identities(client):
    """SEC-2: walk the endpoints a professor can reach and scan every response for student IDs or names."""
    login(client, "professor")
    leak = re.compile(r"\bST\d{3,5}\b|Student \d{3,5}")
    seen = []
    for sid in ("baseline", "faculty", "diagnostic", "shortfall"):
        for path in (f"/scenarios/{sid}", f"/scenarios/{sid}/my-classes", f"/proposals?scenario_id={sid}"):
            r = client.get("/api" + path)
            seen.append(path)
            assert r.status_code in (200, 403, 404) and not leak.search(r.text), path
    data = client.get("/api/scenarios/faculty").json()
    s = data["sections"][0]
    for day in range(5):
        r = client.post("/api/scenarios/faculty/preview-change", json=dict(section_id=s["id"], meeting_index=0, day=day, start=600, alternatives=True))
        assert not leak.search(r.text)
    r = client.post("/api/scenarios/faculty/changes", json=dict(section_id=s["id"], meeting_index=0, day=(s["meetings"][0]["day"] + 1) % 5, start=600, reason="Leak check"))
    assert not leak.search(r.text)
    r = client.post("/api/scenarios/faculty/optimize", json=dict(max_changes=2, seconds=5))
    assert not leak.search(r.text)
    r = client.post("/api/scenarios/faculty/free-slots", json=dict(sections=[s["id"]], duration=60))
    assert not leak.search(r.text)
    assert not leak.search(client.get("/api/proposals?scenario_id=faculty").text)
    assert len(seen) == 12
