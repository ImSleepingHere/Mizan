"""Synthetic, reproducible fixtures: never presented as institutional data."""
from .models import Semester


def generate_faculty(seed=2027):
    """'Faculty week' (spec §18): mixed rosters, Mon/Wed meetings, 75/90-minute courses, and the demo
    professor (P001) teaching S087-S091. Valid by construction; checked in tests/test_scope.py."""
    import random
    rng = random.Random(seed)
    departments = ["Computing", "Business", "Engineering", "Design"]
    skills = ["computing", "business", "engineering", "design"]
    hours = [{"day": d, "start": 480, "end": 1080} for d in range(5)]
    long_courses = {f"C{i:03}": 75 for i in (23, 31, 44, 47, 58, 66)} | {f"C{i:03}": 90 for i in (27, 38, 50, 62, 71)}
    courses = []
    for i in range(80):
        dep, cid = i % 4, f"C{i+1:03}"
        courses.append(dict(id=cid, name=f"{departments[dep]} {'Foundations' if i < 20 else 'Studio'} {i+1}",
                            name_ar=f"{'أساسيات' if i < 20 else 'دراسات'} {['الحوسبة','الأعمال','الهندسة','التصميم'][dep]} {i+1}",
                            department=departments[dep], competency=skills[dep], duration=long_courses.get(cid, 60),
                            prerequisites=[] if i < 20 else [f"C{dep+1:03}"]))
    duration = {c["id"]: c["duration"] for c in courses}
    professors = [dict(id=f"P{i+1:03}", name=f"Dr. Faculty {i+1:02}", department=departments[(i//2) % 4],
                       competencies=skills.copy(), contracted_minutes=900, availability=hours) for i in range(50)]
    rooms = [dict(id=f"R{i+1:03}", name=f"{'North' if i < 20 else 'South'} · {101+i}", capacity=80, availability=hours) for i in range(39)]
    rooms.append(dict(id="R040", name="Main hall · 200", capacity=200, availability=hours))  # large enough to merge two sections
    patterns = [(0, 2), (1, 3), (2, 4), (0, 3), (1, 4)]  # Sun/Tue, Mon/Wed, Tue/Thu, Sun/Wed, Mon/Thu
    starts = [480, 600, 780, 900, 960]  # 90-minute meetings still end by 17:30
    # The demo professor's own week: realistic, mixed days and lengths. S087 and S089 are two sections of one course.
    fixed = {"S087": ("C047", (0, 2), 600), "S088": ("C048", (2, 4), 780), "S089": ("C047", (1, 3), 900),
             "S090": ("C050", (0, 4), 690), "S091": ("C051", (1, 3), 480)}
    sections, busy_room, busy_prof = [], {}, {}

    def windows(pattern, start, cid):
        return [(d, start, start + duration[cid]) for d in pattern]

    def free(table, key, ws):
        return all(not (d == d2 and s < e2 and s2 < e) for d, s, e in ws for d2, s2, e2 in table.get(key, []))

    for n in range(100):
        sid = f"S{n+1:03}"
        if sid in fixed:
            cid, pattern, start = fixed[sid]
            prof = "P001"
        else:
            cid = f"C{21 + (n % 60):03}"
            pattern, start = patterns[n % 5], starts[(n // 5) % 5]
            prof = f"P{2 + n // 2 % 49:03}"
        ws = windows(pattern, start, cid)
        if not free(busy_prof, prof, ws):
            prof = next(p["id"] for p in professors[1:] if free(busy_prof, p["id"], ws))
        room = next(r["id"] for r in rooms if free(busy_room, r["id"], ws))
        busy_prof.setdefault(prof, []).extend(ws)
        busy_room.setdefault(room, []).extend(ws)
        sections.append(dict(id=sid, course_id=cid, professor_id=prof, room_id=room, capacity=80,
                             meetings=[dict(day=d, start=s, end=e) for d, s, e in ws]))
    by_id = {s["id"]: s for s in sections}
    seats = {s["id"]: 0 for s in sections}
    students = []
    for k in range(1500):
        dep = k % 4
        order = [s["id"] for s in sections]
        rng.shuffle(order)
        # Two thirds of students take at least one of the professor's sections, so rosters overlap without being identical.
        if k % 3 != 2:
            mine = [x for x in fixed if x != "S089"] if k % 2 else [x for x in fixed if x != "S087"]
            order = rng.sample(mine, 2) + order
        chosen, taken, courses_taken = [], [], set()
        for sid in order:
            s = by_id[sid]
            ws = [(m["day"], m["start"], m["end"]) for m in s["meetings"]]
            if seats[sid] >= s["capacity"] or s["course_id"] in courses_taken:
                continue
            if any(d == d2 and a < e2 and a2 < e for d, a, e in ws for d2, a2, e2 in taken):
                continue
            chosen.append(sid); taken += ws; courses_taken.add(s["course_id"]); seats[sid] += 1
            if len(chosen) == 4:
                break
        students.append(dict(id=f"ST{k+1:04}", name=f"Student {k+1:04}", cohort=f"{departments[dep]} · {k % 20 + 1:02}",
                             completed=[f"C{i+1:03}" for i in range(20)], sections=chosen))
    return Semester(name="Faculty week · mixed rosters", kind="faculty",
                    provenance="Synthetic dataset · fixed generation seed · not university records",
                    seed=seed, courses=courses, students=students, professors=professors, rooms=rooms, sections=sections)


def generate(kind="baseline", groups=20, per_group=75):
    if kind == "faculty":
        return generate_faculty()
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
