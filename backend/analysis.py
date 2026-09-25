from collections import defaultdict
from math import ceil
from .models import Semester, Section


def overlaps(a, b):
    return a.day == b.day and a.start < b.end and b.start < a.end


def available(meeting, windows):
    return any(w.day == meeting.day and w.start <= meeting.start and meeting.end <= w.end for w in windows)


def indexes(data):
    return ({x.id: x for x in data.courses}, {x.id: x for x in data.professors}, {x.id: x for x in data.rooms})


def enrollments(data):
    result = defaultdict(list)
    for student in data.students:
        for sid in student.sections:
            result[sid].append(student.id)
    return result


def validate(data: Semester):
    courses, profs, rooms = indexes(data)
    roster = enrollments(data)
    issues = []
    def add(code, ids, detail):
        issues.append(dict(code=code, records=ids, detail=detail))
    load = defaultdict(int)
    resources = defaultdict(list)
    for section in data.sections:
        c, p, r = courses[section.course_id], profs[section.professor_id], rooms[section.room_id]
        if len(roster[section.id]) > section.capacity or section.capacity > r.capacity:
            add("CAPACITY", [section.id, r.id], "Enrollment / section capacity exceeds the available capacity")
        if c.room_type != r.type:
            add("ROOM_TYPE", [section.id, r.id], "Required facilities are unavailable")
        if c.competency not in p.competencies:
            add("COMPETENCY", [section.id, p.id], "Instructor is not qualified for this course")
        if len(section.meetings) != c.meetings_per_week:
            add("MEETING_PATTERN", [section.id], "Required number of weekly meetings is not preserved")
        if len({m.day for m in section.meetings}) != len(section.meetings):
            add("MEETING_PATTERN", [section.id], "Repeated meetings require distinct teaching days")
        for m in section.meetings:
            load[p.id] += m.end - m.start
            if m.end - m.start != c.duration:
                add("DURATION", [section.id], "Required instructional duration is not preserved")
            if m.start < data.policy.open_minute or m.end > data.policy.close_minute or any(overlaps(m, b) for b in data.policy.blocked):
                add("BLOCKED_TIME", [section.id], "Meeting is outside approved teaching windows")
            for label, resource in [("PROFESSOR", p), ("ROOM", r)]:
                if not available(m, resource.availability):
                    add(label+"_AVAILABILITY", [section.id, resource.id], "Resource is unavailable")
                resources[(label, resource.id)].append((section.id, m))
            for student_id in roster[section.id]:
                resources[("STUDENT", student_id)].append((section.id, m))
    for (kind, rid), meetings in resources.items():
        ordered = sorted(meetings, key=lambda x: (x[1].day, x[1].start))
        for i, (sid, m) in enumerate(ordered):
            for other_id, other in ordered[i+1:]:
                if other.day != m.day or other.start >= m.end:
                    break
                if overlaps(m, other):
                    add(kind+"_OVERLAP", [rid, sid, other_id], "Simultaneous meetings")
    for pid, minutes in load.items():
        if minutes > profs[pid].contracted_minutes:
            add("CONTRACTED_HOURS", [pid], f"Assigned {minutes} minutes; contracted {profs[pid].contracted_minutes}")
    sections = {s.id: s for s in data.sections}
    for student in data.students:
        for sid in student.sections:
            course = courses[sections[sid].course_id]
            if not set(course.prerequisites) <= set(student.completed):
                add("PREREQUISITE", [student.id, sid], "Required completed prerequisites are missing")
    return issues


def gini(values):
    values = sorted(values)
    total, n = sum(values), len(values)
    return round(sum((2*i-n-1)*v for i, v in enumerate(values, 1))/(n*total), 4) if total else 0


def student_metrics(data):
    sections = {s.id: s for s in data.sections}
    pattern_cache, result = {}, []
    for student in data.students:
        key = tuple(sorted(student.sections))
        if key not in pattern_cache:
            days = defaultdict(list)
            for sid in key:
                for m in sections[sid].meetings:
                    days[m.day].append(m)
            gaps, spans = [], []
            for meetings in days.values():
                meetings.sort(key=lambda m: m.start)
                gaps += [max(0, b.start-a.end) for a, b in zip(meetings, meetings[1:])]
                spans.append(max(m.end for m in meetings)-min(m.start for m in meetings))
            components = dict(gap_minutes=sum(gaps), longest_gap=max(gaps, default=0), campus_days=len(days),
                              max_span=max(spans, default=0), fragments=sum(g>0 for g in gaps),
                              irregular=sum(m.start % 30 != 0 or m.end % 30 != 0 for meetings in days.values() for m in meetings))
            # Transparent descriptive score, distinct from the optimizer's policy weights.
            penalties = [(.4, components["gap_minutes"]/1200), (.2, components["longest_gap"]/240),
                         (.15, components["campus_days"]/5), (.15, components["max_span"]/600),
                         (.05, components["fragments"]/10), (.05, components["irregular"]/10)]
            components["score"] = round(100*(1-sum(w*min(1,x) for w,x in penalties)), 1)
            pattern_cache[key] = components
        result.append(dict(id=student.id, cohort=student.cohort, **pattern_cache[key]))
    return result


def metrics(data, issues=None):
    issues = validate(data) if issues is None else issues
    students = student_metrics(data)
    cohorts = defaultdict(list)
    for student in students:
        cohorts[student["cohort"]].append(student)
    n = max(1, len(students))
    workloads = []
    for p in data.professors:
        mins = sum(m.end-m.start for s in data.sections if s.professor_id == p.id for m in s.meetings)
        workloads.append(dict(id=p.id, name=p.name, department=p.department, minutes=mins, contracted_minutes=p.contracted_minutes))
    used = sum(m.end-m.start for s in data.sections for m in s.meetings)
    def permitted_minutes(window):
        start,end=max(window.start,data.policy.open_minute),min(window.end,data.policy.close_minute)
        if end<=start: return 0
        blocked=sorted((max(start,b.start),min(end,b.end)) for b in data.policy.blocked if b.day==window.day and b.end>start and b.start<end)
        last,total=start,0
        for a,b in blocked:
            total+=max(0,a-last)
            last=max(last,b)
        return total+max(0,end-last)
    capacity = sum(permitted_minutes(w) for r in data.rooms for w in r.availability)
    worst = sorted(students, key=lambda x:x["gap_minutes"], reverse=True)[:max(1, ceil(len(students)*.1))]
    return dict(valid=not issues, conflict_count=len(issues), students=len(students), sections=len(data.sections),
                gap_hours=round(sum(s["gap_minutes"] for s in students)/60, 2),
                long_gap_2h=sum(s["longest_gap"] >= 120 for s in students),
                long_gap_4h=sum(s["longest_gap"] >= 240 for s in students),
                average_days=round(sum(s["campus_days"] for s in students)/n, 2),
                average_span=round(sum(s["max_span"] for s in students)/n, 1),
                score=round(sum(s["score"] for s in students)/n,1) if not issues else None,
                worst_decile_gap_hours=round(sum(s["gap_minutes"] for s in worst)/max(1,len(worst))/60,2),
                load_gini=gini([p["minutes"] for p in workloads]),
                room_utilization=round(100*used/capacity,1) if capacity else 0,
                cohorts=[dict(name=k, students=len(v), gap_hours=round(sum(s["gap_minutes"] for s in v)/60,2),
                              average_gap_hours=round(sum(s["gap_minutes"] for s in v)/len(v)/60,2)) for k,v in cohorts.items()],
                workloads=workloads,
                department_load=[dict(department=dep,gini=gini([p["minutes"] for p in workloads if p["department"]==dep]),
                                      most_burdened_decile_minutes=sorted([p["minutes"] for p in workloads if p["department"]==dep],reverse=True)[:max(1,ceil(sum(p["department"]==dep for p in workloads)*.1))]) for dep in sorted({p["department"] for p in workloads})],
                issues=issues[:250], issues_truncated=len(issues)>250,
                metric_version="1.0", score_definition="40% gaps/1200m; 20% longest gap/240m; 15% days/5; 15% span/600m; 5% fragments/10; 5% irregular/10. Each ratio capped at 1.")


def compare(before, after):
    old = {s["id"]: s for s in student_metrics(before)}
    new = student_metrics(after)
    if set(old) != {s["id"] for s in new}:
        raise ValueError("comparison populations differ")
    deltas = [dict(id=s["id"], cohort=s["cohort"], gap_delta=s["gap_minutes"]-old[s["id"]]["gap_minutes"],
                   days_delta=s["campus_days"]-old[s["id"]]["campus_days"]) for s in new]
    baseline = {s.id:s for s in before.sections}
    changes = [dict(section_id=s.id, before=baseline[s.id].model_dump() if s.id in baseline else None, after=s.model_dump())
               for s in after.sections if s.id not in baseline or s != baseline[s.id]]
    worsened = [d for d in deltas if d["gap_delta"]>0 or d["days_delta"]>0]
    return dict(recovered_hours=round(-sum(d["gap_delta"] for d in deltas)/60,2),
                benefiting=sum(d["gap_delta"]<0 or d["days_delta"]<0 for d in deltas),
                worsened=len(worsened), adverse_students=worsened, changes=changes,
                worst_increase_minutes=max((d["gap_delta"] for d in deltas),default=0))


def eligible_students(data, course_id):
    course = next(c for c in data.courses if c.id == course_id)
    existing = {s.id for s in data.sections if s.course_id == course_id}
    return [s for s in data.students if course_id not in s.completed and not existing.intersection(s.sections)
            and set(course.prerequisites) <= set(s.completed)]
