"""Behaviour fixed after the 4 Oct hands-on UX review (IDs refer to docs/reviews/2026-10-04-ux-review.md)."""
import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("MIZAN_DB", str(tmp_path / "ux.sqlite3"))
    monkeypatch.delenv("MIZAN_DEMO_PASSWORD", raising=False)
    with TestClient(app, headers={"X-Mizan-Action": "1"}) as c:
        yield c


def login(c, name):
    assert c.post("/api/login", json={"username": name, "password": "Mizan-demo-2026!"}).status_code == 200


def test_occupancy_agrees_across_roles_without_rosters(client):
    """S02: every role sees the same seat count for a section; students still see no other students."""
    login(client, "admin")
    staff = client.get("/api/scenarios/baseline").json()["enrollment"]
    login(client, "student")
    mine = client.get("/api/scenarios/baseline").json()
    assert mine["enrollment"] and all(mine["enrollment"][s] == staff[s] for s in mine["enrollment"])
    assert len(mine["students"]) == 1
    login(client, "professor")
    prof = client.get("/api/scenarios/baseline").json()
    assert prof["students"] == [] and all(prof["enrollment"][s] == staff[s] for s in prof["enrollment"])


def test_unchanged_meeting_is_not_a_request(client):
    """I02/I03: previewing the current slot says so; submitting it creates nothing."""
    login(client, "professor")
    sec = client.get("/api/scenarios/faculty").json()["sections"][0]
    m = sec["meetings"][0]
    preview = client.post("/api/scenarios/faculty/preview-change", json=dict(section_id=sec["id"], meeting_index=0, day=m["day"], start=m["start"])).json()
    assert preview["unchanged"] is True and preview["recovered_hours"] == 0
    r = client.post("/api/scenarios/faculty/changes", json=dict(section_id=sec["id"], meeting_index=0, day=m["day"], start=m["start"], reason="Same slot"))
    assert r.status_code == 422 and "already scheduled" in r.json()["detail"]
    assert client.get("/api/proposals?scenario_id=faculty").json() == []


def test_stale_proposals_are_flagged_and_can_be_reevaluated(client):
    """C02: after another proposal is published, older ones are marked stale; a meeting change re-runs without retyping."""
    login(client, "admin")
    data = client.get("/api/scenarios/baseline").json()
    s = data["sections"][0]
    move = next(dict(section_id=s["id"], meeting_index=0, day=d, start=st) for d in range(5) for st in range(480, 1020, 60)
                if client.post("/api/scenarios/baseline/preview-change", json=dict(section_id=s["id"], meeting_index=0, day=d, start=st)).json().get("feasible")
                and (d, st) != (s["meetings"][0]["day"], s["meetings"][0]["start"]))
    first = client.post("/api/scenarios/baseline/changes", json=dict(move, reason="First")).json()
    assert first["status"] == "recommended"
    listed = {p["id"]: p for p in client.get("/api/proposals?scenario_id=baseline").json()}
    assert listed[first["id"]]["stale"] is False and listed[first["id"]]["actor_name"] == "Mizan Administrator"
    # Any new timetable version (here: a policy version) makes the proposal outdated.
    assert client.post("/api/scenarios/baseline/policy", json=dict(revision=data["revision"], policy=data["policy"])).status_code == 200
    listed = {p["id"]: p for p in client.get("/api/proposals?scenario_id=baseline").json()}
    assert listed[first["id"]]["stale"] is True
    assert client.post(f"/api/proposals/{first['id']}/approve").status_code == 409
    redo = client.post(f"/api/proposals/{first['id']}/reevaluate")
    assert redo.status_code == 200
    listed = {p["id"]: p for p in client.get("/api/proposals?scenario_id=baseline").json()}
    assert listed[first["id"]]["status"] == "superseded"
    assert listed[redo.json()["id"]]["base_revision"] == 2 and listed[redo.json()["id"]]["analysis"]["request"]["section_id"] == s["id"]


def test_professor_sees_own_optimization_in_their_list(client):
    """I13: an instructor's own optimization stays findable in their request list."""
    login(client, "professor")
    r = client.post("/api/scenarios/faculty/optimize", json=dict(max_changes=2, seconds=5)).json()
    if not r.get("proposal"):
        pytest.skip("no improvement found in this run")
    ids = [p["id"] for p in client.get("/api/proposals?scenario_id=faculty").json()]
    assert r["proposal"]["id"] in ids


def test_audit_entries_name_their_timetable(client):
    """C13: audit rows carry the scenario they belong to."""
    login(client, "admin")
    s = client.get("/api/scenarios/faculty").json()["sections"][0]
    client.post("/api/scenarios/faculty/changes", json=dict(section_id=s["id"], meeting_index=0, day=(s["meetings"][0]["day"] + 1) % 5, start=s["meetings"][0]["start"], reason="Audit"))
    rows = client.get("/api/audit").json()
    created = next(r for r in rows if r["action"] == "proposal_created")
    assert created["scenario_id"] == "faculty" and created["scenario_name"] and created["actor_name"] == "Mizan Administrator"
