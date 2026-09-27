"""Common free-slot finder (spec §18.5): hand-checked fixture, API permissions and the request path."""
import json
import re
import pytest
from fastapi.testclient import TestClient
from backend import local_model
from backend.models import Semester
from backend.solver import common_slots
from backend.main import app
from backend.store import connect

HOURS = [{"day": d, "start": 480, "end": 720} for d in range(5)]


def tiny():
    """08:00-12:00 week. S1 (P1): Sun/Tue 8-9, students A B C. S2 (P1): Mon/Wed 9-10, students D E.
    S3 (P2): Sun/Tue 10-11, students C D. Small rooms seat 4, the hall seats 60."""
    course = lambda i: dict(id=f"C{i}", name=f"Course {i}", name_ar=f"مقرر {i}", department="Computing", competency="computing")
    meet = lambda days, h: [dict(day=d, start=h * 60, end=h * 60 + 60) for d in days]
    return Semester(name="tiny", provenance="test", courses=[course(1), course(2), course(3)],
                    professors=[dict(id=p, name=p, department="Computing", competencies=["computing"], contracted_minutes=600, availability=HOURS) for p in ["P1", "P2"]],
                    rooms=[dict(id="R1", name="R1", capacity=4, availability=HOURS), dict(id="R2", name="R2", capacity=4, availability=HOURS),
                           dict(id="R3", name="Hall", capacity=60, availability=HOURS)],
                    sections=[dict(id="S1", course_id="C1", professor_id="P1", room_id="R1", capacity=4, meetings=meet([0, 2], 8)),
                              dict(id="S2", course_id="C2", professor_id="P1", room_id="R1", capacity=4, meetings=meet([1, 3], 9)),
                              dict(id="S3", course_id="C3", professor_id="P2", room_id="R2", capacity=4, meetings=meet([0, 2], 10))],
                    students=[dict(id=x, name=x, cohort="c", sections=s) for x, s in
                              [("A", ["S1"]), ("B", ["S1"]), ("C", ["S1", "S3"]), ("D", ["S2", "S3"]), ("E", ["S2"])]])


def by_start(result):
    return {(s["day"], s["start"]): s for s in result["slots"]}


def test_hand_checked_ranking_and_counts():
    r = common_slots(tiny(), ["S1"], 60, days=[0], limit=10)
    best = r["slots"][0]
    # Sunday 09:00: everyone free, the professor free, fills C's gap between 9 and 10.
    assert (best["day"], best["start"], best["unavailable"], best["rooms"], best["professor_free"]) == (0, 540, 0, ["R1"], True)
    assert best["added_gap_hours"] == -1.0 and best["extra_campus_days"] == 0
    full = common_slots(tiny(), ["S1"], 60, days=[0], limit=50)
    slots = {s["start"]: s for s in full["slots"]}
    assert slots[480]["unavailable"] == 3 and not slots[480]["professor_free"]  # the section's own class time
    assert r["group_size"] == 3 and "Date-specific exceptions are not checked" in r["note"]
    everything = common_slots(tiny(), ["S1"], 60, days=[0], limit=99)
    assert all(not (a["start"] < b["end"] and b["start"] < a["end"]) for a in everything["slots"] for b in everything["slots"] if a is not b)


def test_student_conflicts_are_counted_not_hidden():
    r = common_slots(tiny(), ["S1"], 60, days=[0], limit=99, earliest=600, latest_end=660)
    assert [(s["start"], s["unavailable"]) for s in r["slots"]] == [(600, 1)]  # C has S3 at 10:00


def test_merge_needs_a_room_for_everyone_and_frees_merged_meetings():
    r = common_slots(tiny(), ["S1", "S2"], 60, days=[1], merge=True, limit=10)
    best = r["slots"][0]
    assert r["group_size"] == 5 and best["rooms"] == ["R3"]  # small rooms seat 4
    starts = {s["start"]: s["unavailable"] for s in r["slots"]}
    assert best["unavailable"] == 0 and starts[540] == 0  # S2's own Monday 09:00 meeting is replaced by the merged lecture
    separate = common_slots(tiny(), ["S1", "S3"], 60, days=[1], same_time_for_all=True, limit=5)
    assert len(separate["slots"][0]["rooms"]) == 2  # one room per section at the same time


def test_forty_five_minute_grid():
    r = common_slots(tiny(), ["S2"], 45, days=[4], limit=99)
    assert all((s["end"] - s["start"]) == 45 and s["start"] % 15 == 0 for s in r["slots"])


# ---------- API and request path ----------

STUDENT_ID = re.compile(r"\bST\d{4}\b")


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("MIZAN_DB", str(tmp_path / "finder.sqlite3"))
    monkeypatch.delenv("MIZAN_DEMO_PASSWORD", raising=False)
    monkeypatch.setattr(local_model, "status", lambda: {"available": True, "coordinator_model": "pretrained"})
    state = {}
    monkeypatch.setattr(local_model, "structured", lambda *a, **k: (json.loads(json.dumps(state["raw"])), {"model": "fake"}))
    with TestClient(app, headers={"X-Mizan-Action": "1"}) as c:
        c.state = state
        yield c


def login(c, name):
    assert c.post('/api/login', json={"username": name, "password": "Mizan-demo-2026!"}).status_code == 200


def test_free_slots_api_permissions_and_privacy(client):
    login(client, "professor")
    r = client.post('/api/scenarios/faculty/free-slots', json={"sections": ["S087", "S089"], "duration": 75, "days": [2], "merge": True})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["group_size"] == 70 and body["slots"][0]["rooms"] and not STUDENT_ID.search(json.dumps(body))
    assert client.post('/api/scenarios/faculty/free-slots', json={"sections": ["S001"], "duration": 60}).status_code == 403
    assert client.post('/api/scenarios/faculty/free-slots', json={"sections": ["S087"], "duration": 60, "merge": True}).status_code == 422
    for name in ["student", "hiring_manager"]:
        login(client, name)
        assert client.post('/api/scenarios/faculty/free-slots', json={"sections": ["S087"], "duration": 60}).status_code == 403
    with connect() as db:
        assert db.execute("SELECT count(*) FROM audit WHERE action='free_slot_search'").fetchone()[0] == 1
        assert db.execute("SELECT count(*) FROM proposals").fetchone()[0] == 0  # finding books nothing


def test_request_finds_slots_with_a_date_note_and_books_nothing(client):
    login(client, "professor")
    client.state["raw"] = {"task": "find_common_slot", "scope": "sections", "date_scope": {"kind": "one_off", "phrase": "next week"},
                           "target_sections": ["S088"], "book_session": True,
                           "slot_search": {"duration": 120, "days": [], "same_time_for_all": False, "group": "target_sections"}}
    body = client.post('/api/requests/interpret', json={"scenario_id": "faculty", "text": "دور لي يوم الاسبوع الجاي كل طلاب سكشن 88 يكونون فاضين ساعتين وخله revision"}).json()
    assert body["next_step"] == "find_slots" and body["date_note"]["ar"]
    assert [u["code"] for u in body["interpretation"]["unsupported"]] == ["EXTRA_SESSION"]
    done = client.post(f'/api/requests/{body["id"]}/confirm', json={})
    assert done.status_code == 200, done.text
    result = done.json()["result"]
    assert result["status"] == "FOUND" and result["duration"] == 120 and result["slots"][0]["group_size"] == 35
    with connect() as db:
        assert db.execute("SELECT count(*) FROM proposals").fetchone()[0] == 0


def test_merge_request_uses_the_section_length(client):
    login(client, "professor")
    client.state["raw"] = {"task": "merge_sections", "scope": "sections", "date_scope": {"kind": "weekly", "phrase": ""},
                           "target_sections": ["S087", "S089"], "day_filter": ["tue"],
                           "slot_search": {"duration": None, "days": ["tue"], "same_time_for_all": True, "group": "target_sections"}}
    body = client.post('/api/requests/interpret', json={"scenario_id": "faculty", "text": "best Tuesday time to merge 87 and 89"}).json()
    assert body["interpretation"]["clarify"] == []  # a merge keeps the section's length, so no question
    result = client.post(f'/api/requests/{body["id"]}/confirm', json={}).json()["result"]
    assert result["merge"] and result["duration"] == 75 and all(s["day"] == 2 for s in result["slots"])
