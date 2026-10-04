"""Edugate exchange: read Al Yamamah schedules (OCR), import after review, optimize, export in the Edugate layout.
Uses invented rows only; no real student's schedule is stored in the repository."""
import pytest
import pymupdf
from fastapi.testclient import TestClient
from backend.main import app
from backend import edugate
from backend.models import Semester

ROWS = [dict(code="MKT 201", code_ar="تسق 201", section="12", activity="نظري", credits=3, days=[0, 2], start=480, end=560, room="B-12"),
        dict(code="FIN 202", code_ar="مال 202", section="17", activity="نظري", credits=3, days=[1, 3], start=800, end=880, room="A-03"),
        dict(code="ARB 202", code_ar="عرب 202", section="31", activity="نظري", credits=2, days=[4], start=990, end=1100, room="COED-02")]


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("MIZAN_DB", str(tmp_path / "edugate.sqlite3"))
    monkeypatch.delenv("MIZAN_DEMO_PASSWORD", raising=False)
    with TestClient(app, headers={"X-Mizan-Action": "1"}) as c:
        yield c


def login(c, name):
    assert c.post("/api/login", json={"username": name, "password": "Mizan-demo-2026!"}).status_code == 200


def test_ocr_readings_are_normalised():
    assert edugate.clean_room("A-OI") == "A-01" and edugate.clean_room("04-A") == "A-04" and edugate.clean_room("COED-II") == "COED-11"
    assert edugate.code_parts("202 عرب") == ("ARB", "202")
    assert edugate.code_parts("نسف 201") == ("MKT", "201")  # dot confusion: نسف has the shape of تسق
    assert edugate.code_parts("MGT 210") == ("MGT", "210")
    assert edugate.match_day("الإننين") == 1 and edugate.match_day("الحمبس") == 4 and edugate.match_day("Wed") == 3
    assert edugate.match_day("العربية") is None
    assert edugate.to_minutes("04", "30", "م") == 990 and edugate.to_minutes("11", "00", "ص") == 660
    assert edugate.to_minutes("12", "20", "م") == 740 and edugate.to_minutes("1", "20") == 800


def test_import_needs_review_permissions_and_complete_rows(client):
    login(client, "chair")
    assert client.post("/api/edugate/import", json=dict(student_id="T1", student_name="A", rows=ROWS)).status_code == 403
    login(client, "admin")
    missing_end = [dict(ROWS[0], end=None)]
    assert client.post("/api/edugate/import", json=dict(student_id="T1", student_name="A", rows=missing_end)).status_code == 422
    twice = [ROWS[0], dict(ROWS[0], section="13")]
    assert client.post("/api/edugate/import", json=dict(student_id="T1", student_name="A", rows=twice)).status_code == 422
    assert client.post("/api/edugate/import", json=dict(student_id="T1", student_name="A", rows=ROWS, scenario_id="baseline")).status_code == 409


def test_import_optimize_and_export(client):
    login(client, "admin")
    r = client.post("/api/edugate/import", json=dict(student_id="T1", student_name="First", term="2026/2027", rows=ROWS)).json()
    assert r["issues"] == [] and r["sections"] == 3
    sid = r["id"]
    body = client.get(f"/api/scenarios/{sid}").json()
    data = Semester.model_validate({k: v for k, v in body.items() if k not in ("id", "revision")})
    assert data.kind == "edugate" and data.term == "2026/2027"
    assert {c.code_ar for c in data.courses} == {"تسق 201", "مال 202", "عرب 202"}
    assert {990, 1100 - 110} <= set(data.policy.allowed_starts) and data.policy.close_minute >= 1100
    # A second student in MKT 201 section 12 shares that section; a new section of FIN is a new section.
    second = [ROWS[0], dict(ROWS[1], section="18", start=890, end=970)]
    r2 = client.post("/api/edugate/import", json=dict(student_id="T2", student_name="Second", rows=second, scenario_id=sid)).json()
    assert r2["revision"] == 2 and r2["students"] == 2 and r2["sections"] == 4
    assert [t["id"] for t in client.get("/api/edugate/timetables").json()] == [sid]
    result = client.post(f"/api/scenarios/{sid}/optimize", json=dict(max_changes=3, seconds=5)).json()
    assert result["status"] in {"OPTIMAL", "FEASIBLE"}
    pdf = client.get(f"/api/edugate/export?scenario_id={sid}&student_id=T1")
    assert pdf.status_code == 200 and pdf.headers["content-type"] == "application/pdf"
    text = pymupdf.open(stream=pdf.content, filetype="pdf")[0].get_text()
    assert "COED-02" in text and "2026/2027" in text and "Edugate registration record" in text
    if result.get("proposal"):
        proposed = client.get(f"/api/edugate/export?scenario_id={sid}&student_id=T1&proposal_id={result['proposal']['id']}")
        assert proposed.status_code == 200
    assert client.get(f"/api/edugate/export?scenario_id={sid}&student_id=NOPE").status_code == 404


def test_students_export_only_their_own_timetable(client):
    login(client, "student")
    assert client.get("/api/edugate/export?scenario_id=baseline&student_id=ST0001").status_code == 200
    assert client.get("/api/edugate/export?scenario_id=baseline&student_id=ST0002").status_code == 403
    assert client.post("/api/edugate/import", json=dict(student_id="T1", student_name="A", rows=ROWS)).status_code == 403


def test_changed_rows_are_marked_against_the_imported_schedule(client):
    login(client, "admin")
    sid = client.post("/api/edugate/import", json=dict(student_id="T1", student_name="A", rows=ROWS)).json()["id"]
    from backend.main import scenario
    _, data = scenario(sid)
    moved = data.model_copy(deep=True)
    moved.sections[0].meetings = [m.model_copy(update=dict(start=m.start + 90, end=m.end + 90)) for m in moved.sections[0].meetings]
    _, rows = edugate.schedule_rows(moved, "T1", original=data)
    assert [r["changed"] for r in rows] == [True, False, False]
    assert rows[0]["time"] == "09:30 ص - 10:50 ص" and rows[0]["days"] == ["الأحد", "الثلاثاء"]


def test_export_reads_back_through_ocr():
    """Round trip: Mizan's own Edugate-layout export is read back by the importer (Windows OCR)."""
    try:
        from backend.edugate_routes import build, ImportBody
        data, _ = build(ImportBody(student_id="T1", student_name="Round Trip", term="2026/2027", rows=ROWS), None)
        result = edugate.read_schedule(edugate.render_schedule_pdf(data, "T1"))
    except edugate.ReadError as e:
        pytest.skip(e.en)
    got = {r["code"]: (r["days"], r["start"], r["end"], r["room"]) for r in result["rows"]}
    assert got == {r["code"]: (r["days"], r["start"], r["end"], r["room"]) for r in ROWS}
    assert result["term"] == "2026/2027"
