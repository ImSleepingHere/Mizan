"""'My classes' scope (spec §18.3) and the Faculty week demo scenario."""
import json
import re
import pytest
from fastapi.testclient import TestClient
from backend.fixtures import generate
from backend.analysis import validate, enrollments
from backend.solver import optimize
from backend.models import Semester
from backend.main import app
from backend.store import connect

STUDENT_ID = re.compile(r"\bST\d{4}\b")


@pytest.fixture(scope="module")
def faculty():
    return generate("faculty")


def test_faculty_scenario_is_valid_and_realistic(faculty):
    assert validate(faculty) == []
    own = sorted(s.id for s in faculty.sections if s.professor_id == "P001")
    assert own == ["S087", "S088", "S089", "S090", "S091"]
    days = {m.day for s in faculty.sections if s.id in own for m in s.meetings}
    assert {1, 3} <= days  # Monday and Wednesday meetings exist
    durations = {m.end - m.start for s in faculty.sections for m in s.meetings}
    assert {60, 75, 90} <= durations
    roster = {sid: set(v) for sid, v in enrollments(faculty).items()}
    assert len({frozenset(roster[s]) for s in own}) == len(own)  # no two identical rosters
    assert roster["S087"] & roster["S088"] and roster["S087"] != roster["S088"]
    assert faculty.sections[86].course_id == faculty.sections[88].course_id  # S087 and S089: two sections of one course
    assert max(r.capacity for r in faculty.rooms) >= len(roster["S087"]) + len(roster["S089"])  # a merge has a room
    assert generate("faculty").model_dump() == faculty.model_dump()  # fixed seed


def test_existing_scenarios_unchanged():
    base = generate("baseline")
    assert [s.id for s in base.sections if s.professor_id == "P001"] == ["S001", "S002", "S003"]
    assert {m.end - m.start for s in base.sections for m in s.meetings} == {60}


def test_optimizer_moves_only_movable_sections(faculty):
    own = {s.id for s in faculty.sections if s.professor_id == "P001"}
    result = optimize(faculty, 5, 10, movable=own)
    assert result["status"] in {"OPTIMAL", "FEASIBLE"}
    candidate = Semester.model_validate(result["candidate"])
    before = {s.id: s for s in faculty.sections}
    moved = {s.id for s in candidate.sections if s != before[s.id]}
    assert moved and moved <= own
    assert validate(candidate) == []


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("MIZAN_DB", str(tmp_path / "scope.sqlite3"))
    monkeypatch.delenv("MIZAN_DEMO_PASSWORD", raising=False)
    with TestClient(app, headers={"X-Mizan-Action": "1"}) as c:
        yield c


def login(c, name):
    assert c.post('/api/login', json={"username": name, "password": "Mizan-demo-2026!"}).status_code == 200


def test_faculty_scenario_is_seeded_next_to_existing_ones(client):
    login(client, "admin")
    ids = [s["id"] for s in client.get('/api/scenarios').json()]
    assert ids == ["baseline", "diagnostic", "shortfall", "faculty"]


def test_professor_improves_own_classes_without_student_identities(client):
    login(client, "professor")
    r = client.post('/api/scenarios/faculty/optimize', json={"max_changes": 30, "seconds": 10})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["scope"] == "own" and body["max_changes_used"] == 5  # capped at the professor's own section count
    changed = {c["section_id"] for c in body["comparison"]["changes"]}
    assert changed and changed <= {"S087", "S088", "S089", "S090", "S091"}
    assert "adverse_students" not in body["comparison"] and "adverse_count" in body["comparison"]
    assert not STUDENT_ID.search(json.dumps(body))
    assert body["proposal"]["status"] == "recommended"
    listed = client.get('/api/proposals', params={"scenario_id": "faculty"}).json()
    assert listed and not STUDENT_ID.search(json.dumps(listed))
    with connect() as db:
        assert db.execute("SELECT revision FROM scenarios WHERE id='faculty'").fetchone()[0] == 1  # nothing published
        assert db.execute("SELECT kind FROM proposals").fetchone()[0] == "own_optimization"
    # The committee still sees the full evidence.
    login(client, "registrar")
    full = client.get('/api/proposals', params={"scenario_id": "faculty"}).json()
    assert STUDENT_ID.search(json.dumps(full))


def test_professor_previews_and_changes_are_redacted(client):
    login(client, "professor")
    conflict = client.post('/api/scenarios/faculty/preview-change', json={"section_id": "S088", "meeting_index": 0, "day": 0, "start": 600}).json()
    assert conflict["feasible"] is False and conflict["new_issue_count"] > 0
    assert not STUDENT_ID.search(json.dumps(conflict))
    assert any(i.get("student_count") for i in conflict["new_issues"])
    saved = client.post('/api/scenarios/faculty/changes', json={"section_id": "S088", "meeting_index": 0, "day": 0, "start": 600, "reason": "Conflict check"}).json()
    assert saved["status"] == "invalid" and not STUDENT_ID.search(json.dumps(saved))


def test_my_classes_aggregates_and_access(client):
    login(client, "professor")
    info = client.get('/api/scenarios/faculty/my-classes').json()
    assert [s["id"] for s in info["sections"]] == ["S087", "S088", "S089", "S090", "S091"]
    assert info["students"] > 0 and info["conflicts"] == 0 and info["teaching_minutes"] <= info["contracted_minutes"]
    assert not STUDENT_ID.search(json.dumps(info))
    for name in ["registrar", "student", "hiring_manager"]:
        login(client, name)
        assert client.get('/api/scenarios/faculty/my-classes').status_code == 403
    login(client, "student")
    assert client.post('/api/scenarios/faculty/optimize', json={"max_changes": 1, "seconds": 5}).status_code == 403
    login(client, "chair")
    assert client.post('/api/scenarios/faculty/optimize', json={"max_changes": 1, "seconds": 5}).status_code == 403
