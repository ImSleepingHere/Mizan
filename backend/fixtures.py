"""Synthetic, reproducible fixtures: never presented as institutional data."""
from .models import Semester


def generate(kind="baseline", groups=20, per_group=75):
    departments = ["Computing", "Business", "Engineering", "Design"]
    skills = ["computing", "business", "engineering", "design"]
    hours = [{"day": d, "start": 480, "end": 1080} for d in range(5)]
    courses = []
    for i in range(80):
        dep = i % 4
        courses.append(dict(id=f"C{i+1:03}", name=f"{departments[dep]} {'Foundations' if i < 20 else 'Studio'} {i+1}",
                            name_ar=f"{'أساسيات' if i < 20 else 'دراسات'} {['الحوسبة','الأعمال','الهندسة','التصميم'][dep]} {i+1}",
                            department=departments[dep], competency=skills[dep],
                            prerequisites=[] if i < 20 else [f"C{dep+1:03}"]))
    professors = [dict(id=f"P{i+1:03}", name=f"Dr. Faculty {i+1:02}", department=departments[(i//2)%4],
                       competencies=skills.copy(), contracted_minutes=480, availability=hours) for i in range(50)]
    rooms = [dict(id=f"R{i+1:03}", name=f"{'North' if i<20 else 'South'} · {101+i}", capacity=80, availability=hours) for i in range(40)]
    sections, students = [], []
    for g in range(groups):
        cohort_sections = []
        for j, start in enumerate([480, 600, 780, 900, 1020]):
            sid = f"S{g*5+j+1:03}"
            cohort_sections.append(sid)
            ci = 20 + ((g*5+j) % 60)
            sections.append(dict(id=sid, course_id=f"C{ci+1:03}", professor_id=f"P{g*2+j//3+1:03}",
                                 room_id=f"R{g+1:03}", capacity=80,
                                 meetings=[dict(day=d, start=start, end=start+60) for d in [g%3, g%3+2]]))
        for n in range(per_group):
            students.append(dict(id=f"ST{g*per_group+n+1:04}", name=f"Student {g*per_group+n+1:04}",
                                 cohort=f"{departments[g%4]} · {g+1:02}", completed=[f"C{i+1:03}" for i in range(20)], sections=cohort_sections))
    demands = []
    if kind == "diagnostic":
        sections[1]["meetings"] = [dict(m) for m in sections[0]["meetings"]]
        rooms[0]["capacity"] = 30
    if kind == "shortfall":
        courses[-1]["competency"] = "machine_learning"
        for p in professors:
            if p["id"] in ["P049", "P050"]:
                p["competencies"].append("machine_learning")
                p["contracted_minutes"] = 120
        # Keep the baseline teaching assignments valid; the unmet demand is separate.
        for s in sections:
            if s["course_id"] == "C080":
                s["course_id"] = "C021"
        demands = [dict(id="D001", course_id="C080", sections=3, students=[s["id"] for s in students[:112]])]
    return Semester(name={"baseline":"Fall 2026 · Baseline", "diagnostic":"Conflict diagnostics", "shortfall":"Teaching capacity shortfall"}[kind],
                    kind=kind, provenance="Synthetic dataset · fixed generation seed · not university records",
                    courses=courses, students=students, professors=professors, rooms=rooms, sections=sections, demands=demands)
