import json
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.store import connect
from backend import local_model, agent_engine as ae


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("MIZAN_DB", str(tmp_path / "preview.sqlite3"))
    monkeypatch.delenv("MIZAN_DEMO_PASSWORD", raising=False)
    with TestClient(app, headers={"X-Mizan-Action": "1"}) as c:
        assert c.post('/api/login', json={"username": "admin", "password": "Mizan-demo-2026!"}).status_code == 200
        yield c


def test_preview_matches_change_validation_and_saves_nothing(client):
    feasible = client.post('/api/scenarios/baseline/preview-change', json={"section_id": "S001", "meeting_index": 0, "day": 0, "start": 540})
    assert feasible.status_code == 200, feasible.text
    assert feasible.json()["feasible"] is True and feasible.json()["new_issue_count"] == 0
    conflict = client.post('/api/scenarios/baseline/preview-change', json={"section_id": "S001", "meeting_index": 0, "day": 0, "start": 600}).json()
    assert conflict["feasible"] is False and conflict["new_issue_count"] > 0
    # The saved-proposal path agrees with the preview.
    saved = client.post('/api/scenarios/baseline/changes', json={"section_id": "S001", "meeting_index": 0, "day": 0, "start": 600, "reason": "Conflict example"}).json()
    assert saved["status"] == "invalid"
    with connect() as db:
        assert db.execute("SELECT count(*) FROM proposals").fetchone()[0] == 1  # only the explicit change request
        assert db.execute("SELECT revision FROM scenarios WHERE id='baseline'").fetchone()[0] == 1


def test_preview_role_restrictions(client):
    sections = client.get('/api/scenarios/baseline').json()["sections"]
    other = next(s["id"] for s in sections if s["professor_id"] != "P001")
    client.post('/api/logout', json={})
    assert client.post('/api/login', json={"username": "student", "password": "Mizan-demo-2026!"}).status_code == 200
    assert client.post('/api/scenarios/baseline/preview-change', json={"section_id": "S001", "meeting_index": 0, "day": 0, "start": 540}).status_code == 403
    client.post('/api/logout', json={})
    assert client.post('/api/login', json={"username": "professor", "password": "Mizan-demo-2026!"}).status_code == 200
    own = client.get('/api/scenarios/baseline').json()["sections"][0]["id"]
    assert client.post('/api/scenarios/baseline/preview-change', json={"section_id": own, "meeting_index": 0, "day": 1, "start": 540}).status_code == 200
    assert client.post('/api/scenarios/baseline/preview-change', json={"section_id": other, "meeting_index": 0, "day": 1, "start": 540}).status_code == 403


def test_adapter_applies_only_to_coordinator(monkeypatch):
    calls = []
    monkeypatch.setattr(local_model, 'coordinator_adapter', lambda: {"id": 0, "path": "mizan-coordinator-lora.gguf"})
    def fake(system, content, schema, timeout=90, adapter_id=None, compact=False):
        calls.append(dict(system=system, adapter_id=adapter_id, compact=compact))
        action = "delegate" if "Coordinator" in system else "analyze_student_experience"
        return {"action": action, "agent": "student", "max_changes": 0, "disposition": "needs_review"}, {}
    monkeypatch.setattr(local_model, 'structured', fake)
    ctx = {"pending_specialists": ["student"], "user_limit": 5}
    ae.model_decision('coordinator', ctx, ['delegate'])
    ae.model_decision('student', ctx, ['analyze_student_experience', 'report'])
    assert calls[0]["adapter_id"] == 0 and calls[0]["compact"] and calls[0]["system"] == ae.COORDINATOR_TUNED_PROMPT
    assert calls[1]["adapter_id"] is None and not calls[1]["compact"] and "Student Experience" in calls[1]["system"]


def test_adapter_rollback_switch(monkeypatch):
    monkeypatch.setenv('MIZAN_COORDINATOR_ADAPTER', '0')
    monkeypatch.setattr(local_model, 'adapters', lambda max_age=30: [{"id": 0, "path": "x/mizan-coordinator-lora.gguf"}])
    assert local_model.coordinator_adapter() is None
    monkeypatch.setenv('MIZAN_COORDINATOR_ADAPTER', '1')
    assert local_model.coordinator_adapter()["id"] == 0


def test_tuned_prompt_matches_training_prompt():
    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'training' / 'coordinator'))
    try:
        import benchmark
    except ImportError:
        pytest.skip('training files not present')
    assert ae.COORDINATOR_TUNED_PROMPT == benchmark.PROMPT
