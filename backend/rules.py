"""Request-scoped scheduling rules (spec §18.4).

A confirmed interpretation becomes a versioned RuleSet. The optimizer applies it as hard constraints
(option filters + CP-SAT constraints); check_rules() verifies any candidate independently of the solver.
Rules apply only to the sections in scope; every other section stays fixed.
"""
from collections import defaultdict
from typing import Literal
from pydantic import Field
from .models import StrictModel, Window, Section
from .analysis import available, overlaps, indexes

DAY_EN = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"]
DAY_AR = ["الأحد", "الاثنين", "الثلاثاء", "الأربعاء", "الخميس"]
DAY_KEYS = ["sun", "mon", "tue", "wed", "thu"]


def hhmm(minutes):
    return f"{minutes // 60:02}:{minutes % 60:02}"


class TimeRule(StrictModel):
    earliest_start: int | None = None
    latest_start: int | None = None
    latest_end: int | None = None
    days: list[int] = []


class ProtectRule(StrictModel):
    section: str
    days: list[int] = []


class BreakRule(StrictModel):
    minutes: int = Field(ge=5, le=480)
    days: list[int] = []
    kind: Literal["between_each", "one_block"]
    applies_to: Literal["professor", "students"]


class DayMove(StrictModel):
    from_day: int = Field(ge=0, le=4)
    to_day: int = Field(ge=0, le=4)


class RuleSet(StrictModel):
    version: str = "1.0"
    scope_sections: list[str]
    max_changes: int = Field(ge=0, le=30)
    windows: list[TimeRule] = []
    protected: list[ProtectRule] = []
    locked_days: list[int] = []
    keep_days: bool = False
    keep_time: bool = False
    keep_room: bool = False
    breaks: list[BreakRule] = []
    day_to_empty: DayMove | None = None
    must_change: list[str] = []
    must_change_room: list[str] = []
    professors: list[str] = []  # whose breaks are meant when a break applies to "professor"


# ---------- labels (bilingual, used for "times split by rule X" and diagnoses) ----------

def _days(days, ar):
    names = DAY_AR if ar else DAY_EN
    return ("، " if ar else ", ").join(names[d] for d in days)


def rule_items(rules: RuleSet):
    """Atomic rules with stable IDs and bilingual labels, in the order they are reported."""
    items = []
    for i, w in enumerate(rules.windows):
        en, ar = [], []
        if w.earliest_start is not None: en.append(f"start at or after {hhmm(w.earliest_start)}"); ar.append(f"البداية من {hhmm(w.earliest_start)}")
        if w.latest_start is not None: en.append(f"start by {hhmm(w.latest_start)}"); ar.append(f"البداية قبل أو عند {hhmm(w.latest_start)}")
        if w.latest_end is not None: en.append(f"finish by {hhmm(w.latest_end)}"); ar.append(f"الانتهاء قبل {hhmm(w.latest_end)}")
        if w.days: en.append(f"on {_days(w.days, False)}"); ar.append(f"يوم {_days(w.days, True)}")
        items.append(dict(id=f"window:{i}", en="Time window: " + ", ".join(en), ar="نافذة زمنية: " + "، ".join(ar)))
    for i, p in enumerate(rules.protected):
        items.append(dict(id=f"protected:{i}", en=f"Keep {p.section} unchanged" + (f" on {_days(p.days, False)}" if p.days else ""),
                          ar=f"عدم تغيير {p.section}" + (f" يوم {_days(p.days, True)}" if p.days else "")))
    if rules.locked_days:
        items.append(dict(id="locked_days", en=f"Don't touch {_days(rules.locked_days, False)}", ar=f"عدم المساس بمحاضرات {_days(rules.locked_days, True)}"))
    for key, en, ar in [("keep_days", "Keep the days", "الإبقاء على الأيام"), ("keep_time", "Keep the start times", "الإبقاء على أوقات البداية"),
                        ("keep_room", "Keep the rooms", "الإبقاء على القاعات")]:
        if getattr(rules, key):
            items.append(dict(id=key, en=en, ar=ar))
    for i, b in enumerate(rules.breaks):
        who_en, who_ar = ("the professor", "الأستاذ") if b.applies_to == "professor" else ("students", "الطلاب")
        days_en = f" on {_days(b.days, False)}" if b.days else ""
        days_ar = f" يوم {_days(b.days, True)}" if b.days else ""
        items.append(dict(id=f"break:{i}",
                          en=(f"At least {b.minutes} min between classes for {who_en}" if b.kind == "between_each" else f"One free block of {b.minutes} min for {who_en}") + days_en,
                          ar=(f"{b.minutes} دقيقة على الأقل بين المحاضرات لـ{who_ar}" if b.kind == "between_each" else f"فترة فراغ واحدة {b.minutes} دقيقة لـ{who_ar}") + days_ar))
    if rules.day_to_empty:
        f, t = rules.day_to_empty.from_day, rules.day_to_empty.to_day
        items.append(dict(id="day_to_empty", en=f"Move {DAY_EN[f]} classes to {DAY_EN[t]}", ar=f"نقل محاضرات {DAY_AR[f]} إلى {DAY_AR[t]}"))
    if rules.must_change:
        items.append(dict(id="must_change", en=f"Find a new time for {', '.join(rules.must_change)}", ar=f"إيجاد وقت جديد لـ{'، '.join(rules.must_change)}"))
    if rules.must_change_room:
        items.append(dict(id="must_change_room", en=f"New room for {', '.join(rules.must_change_room)}", ar=f"قاعة جديدة لـ{'، '.join(rules.must_change_room)}"))
    items.append(dict(id="max_changes", en=f"Change at most {rules.max_changes} sections", ar=f"تغيير {rules.max_changes} شعب كحد أقصى"))
    return items


def without(rules: RuleSet, rule_id: str) -> RuleSet:
    """The same rule set with one atomic rule removed (for infeasibility diagnosis)."""
    r = rules.model_copy(deep=True)
    kind, _, index = rule_id.partition(":")
    if kind == "window": r.windows.pop(int(index))
    elif kind == "protected": r.protected.pop(int(index))
    elif kind == "break": r.breaks.pop(int(index))
    elif kind == "locked_days": r.locked_days = []
    elif kind in {"keep_days", "keep_time", "keep_room"}: setattr(r, kind, False)
    elif kind == "day_to_empty": r.day_to_empty = None
    elif kind == "must_change": r.must_change = []
    elif kind == "must_change_room": r.must_change_room = []
    elif kind == "max_changes": r.max_changes = min(30, len(r.scope_sections))
    return r


# ---------- from a confirmed interpretation ----------

def from_interpretation(interp, resolution, data, user):
    """Build the rule set for a confirmed interpretation. Raises ValueError for rules the solver cannot apply yet."""
    def minutes(v):
        if v is None: return None
        h, m = v.split(":"); return int(h) * 60 + int(m)
    def days(keys): return sorted({DAY_KEYS.index(k) for k in keys})
    scope = list(resolution["sections"])
    targets = [s for s in interp.target_sections if s in scope]
    default_changes = min(len(scope), 5) if scope else 0
    rules = RuleSet(scope_sections=scope, max_changes=min(30, interp.max_changes if interp.max_changes is not None else max(1, default_changes)),
                    locked_days=days(interp.locked_days), keep_days=interp.keep_days, keep_time=interp.keep_time, keep_room=interp.keep_room,
                    protected=[ProtectRule(section=p["section"], days=days(p["days"])) for p in interp.protected_sections])
    w = interp.allowed_time_window
    if w:
        rules.windows.append(TimeRule(earliest_start=minutes(w.earliest_start), latest_start=minutes(w.latest_start),
                                      latest_end=minutes(w.latest_end), days=days(w.days)))
    b = interp.min_break
    if b:
        if b.kind == "one_block" and b.applies_to == "students":
            raise ValueError("A free block for students is not supported by the solver yet")
        rules.breaks.append(BreakRule(minutes=b.minutes, days=days(b.days), kind=b.kind, applies_to=b.applies_to))
        if b.applies_to == "professor":
            sections = {s.id: s for s in data.sections}
            rules.professors = [user["professor_id"]] if user["role"] == "professor" else sorted({sections[s].professor_id for s in scope})
    if interp.day_to_empty:
        rules.day_to_empty = DayMove(from_day=DAYS_INDEX[interp.day_to_empty.from_day], to_day=DAYS_INDEX[interp.day_to_empty.to_day])
    if interp.task == "reschedule_with_rules" and targets and not (rules.windows or rules.breaks or rules.day_to_empty):
        # Named sections with no rule to satisfy: the request is to find them another time.
        interp = interp.model_copy(update=dict(task="move_meeting"))
    if interp.task == "move_meeting":
        rules.must_change = targets or scope[:1]
        rules.max_changes = max(rules.max_changes, 1)
        if interp.day_filter:
            # "another time on Thursday": the section's meetings on other days stay where they are.
            wanted = set(days(interp.day_filter))
            sections = {s.id: s for s in data.sections}
            for sid in rules.must_change:
                other = sorted({m.day for m in sections[sid].meetings} - wanted)
                if other:
                    rules.protected.append(ProtectRule(section=sid, days=other))
    if interp.task == "change_room":
        rules.must_change_room = targets
        rules.keep_days = rules.keep_days or interp.keep_time
    return rules


DAYS_INDEX = {k: i for i, k in enumerate(DAY_KEYS)}


# ---------- solver side: option generation and filtering ----------

def fixed_meeting(rules, section_id, meeting):
    return meeting.day in rules.locked_days or any(p.section == section_id and (not p.days or meeting.day in p.days) for p in rules.protected)


def window_ok(w: TimeRule, m):
    if w.days and m.day not in w.days:
        return True
    return ((w.earliest_start is None or m.start >= w.earliest_start) and (w.latest_start is None or m.start <= w.latest_start)
            and (w.latest_end is None or m.end <= w.latest_end))


def option_ok(rules, before: Section, option: Section):
    any_fixed = any(fixed_meeting(rules, before.id, m) for m in before.meetings)
    if (rules.keep_room or any_fixed) and option.room_id != before.room_id:
        return False  # a room change would also move a protected or locked meeting
    if before.id in rules.must_change_room and option.room_id == before.room_id:
        return False
    if before.id in rules.must_change and option == before:
        return False
    for b, a in zip(before.meetings, option.meetings):
        if fixed_meeting(rules, before.id, b):
            if a != b:
                return False
            continue
        if (rules.keep_days and a.day != b.day) or (rules.keep_time and a.start != b.start):
            return False
        if not all(window_ok(w, a) for w in rules.windows):
            return False
        if rules.day_to_empty:
            if a.day == rules.day_to_empty.from_day:
                return False
            if b.day == rules.day_to_empty.from_day and a.day != rules.day_to_empty.to_day:
                return False
    return True


def split_options(data, section):
    """Per-meeting alternatives: one meeting moves on its own day, the others stay (only used when a rule needs it)."""
    courses, profs, rooms = indexes(data)
    prof, room = profs[section.professor_id], rooms[section.room_id]
    starts = sorted(set(data.policy.allowed_starts + [m.start for m in section.meetings]))
    out = []
    for i, m in enumerate(section.meetings):
        duration = m.end - m.start
        for start in starts:
            if start == m.start or start < data.policy.open_minute or start + duration > data.policy.close_minute:
                continue
            new = Window(day=m.day, start=start, end=start + duration)
            if not available(new, prof.availability) or not available(new, room.availability) or any(overlaps(new, b) for b in data.policy.blocked):
                continue
            meetings = list(section.meetings); meetings[i] = new
            out.append(section.model_copy(update=dict(meetings=meetings)))
    return out


def needs_split(rules, section):
    """True when a rule concerns only some of this section's meeting days."""
    days = {m.day for m in section.meetings}
    limited = [set(w.days) for w in rules.windows if w.days] + [set(b.days) for b in rules.breaks if b.days] + \
              [set(p.days) for p in rules.protected if p.section == section.id and p.days] + ([set(rules.locked_days)] if rules.locked_days else [])
    return any(0 < len(days & d) < len(days) for d in limited)


def is_split(before, option):
    return len({m.start for m in option.meetings}) > 1 and len({m.start for m in before.meetings}) == 1


def split_reasons(rules, before, after):
    """Which rules make a section's meetings start at different times (shown on the proposal)."""
    days = {m.day for m in before.meetings}
    reasons = []
    for item in rule_items(rules):
        kind, _, index = item["id"].partition(":")
        d = set()
        if kind == "window": d = set(rules.windows[int(index)].days)
        elif kind == "break": d = set(rules.breaks[int(index)].days)
        elif kind == "protected" and rules.protected[int(index)].section == before.id: d = set(rules.protected[int(index)].days)
        elif kind == "locked_days": d = set(rules.locked_days)
        if d and 0 < len(days & d) < len(days):
            reasons.append(dict(id=item["id"], en=item["en"], ar=item["ar"]))
    return reasons


# ---------- independent checker (does not use the solver's filters) ----------

def check_rules(before, after, rules: RuleSet):
    """Verify a candidate against the rule set. Returns a list of violations (empty = compliant)."""
    violations = []
    def add(rule, section, detail):
        violations.append(dict(rule=rule, section=section, detail=detail))
    old = {s.id: s for s in before.sections}
    new = {s.id: s for s in after.sections}
    scope = set(rules.scope_sections)
    changed = [sid for sid in new if sid in old and new[sid] != old[sid]]
    for sid in changed:
        if sid not in scope:
            add("scope", sid, "A section outside the request's scope changed")
    if len(changed) > rules.max_changes:
        add("max_changes", None, f"{len(changed)} sections changed; limit {rules.max_changes}")
    for sid in rules.must_change:
        if sid in new and new[sid] == old.get(sid):
            add("must_change", sid, "The section was not moved")
    for sid in rules.must_change_room:
        if sid in new and new[sid].room_id == old[sid].room_id:
            add("must_change_room", sid, "The room did not change")
    for sid in scope:
        b_sec, a_sec = old[sid], new[sid]
        if rules.keep_room and a_sec.room_id != b_sec.room_id:
            add("keep_room", sid, "Room changed")
        held = [m for m in b_sec.meetings if m.day in rules.locked_days or any(p.section == sid and (not p.days or m.day in p.days) for p in rules.protected)]
        if held and a_sec.room_id != b_sec.room_id:
            add("protected" if any(p.section == sid for p in rules.protected) else "locked_days", sid, "Room changed for a protected or locked meeting")
        for i, (b, a) in enumerate(zip(b_sec.meetings, a_sec.meetings)):
            protected = [p for p in rules.protected if p.section == sid and (not p.days or b.day in p.days)]
            if protected or b.day in rules.locked_days:
                if a != b:
                    add("protected" if protected else "locked_days", sid, f"Meeting {i + 1} changed")
                continue
            if rules.keep_days and a.day != b.day: add("keep_days", sid, f"Meeting {i + 1} changed day")
            if rules.keep_time and a.start != b.start: add("keep_time", sid, f"Meeting {i + 1} changed start time")
            for k, w in enumerate(rules.windows):
                if w.days and a.day not in w.days:
                    continue
                if w.earliest_start is not None and a.start < w.earliest_start: add(f"window:{k}", sid, f"Starts {hhmm(a.start)}, before {hhmm(w.earliest_start)}")
                if w.latest_start is not None and a.start > w.latest_start: add(f"window:{k}", sid, f"Starts {hhmm(a.start)}, after {hhmm(w.latest_start)}")
                if w.latest_end is not None and a.end > w.latest_end: add(f"window:{k}", sid, f"Ends {hhmm(a.end)}, after {hhmm(w.latest_end)}")
            if rules.day_to_empty and a.day == rules.day_to_empty.from_day:
                add("day_to_empty", sid, f"Still meets on {DAY_EN[a.day]}")
    for k, b in enumerate(rules.breaks):
        # A break rule binds only what the request can move: two meetings of sections outside the scope
        # are fixed, so a short break between them is not this request's to fix.
        for label, groups in _break_groups(after, rules, b).items():
            for day in (b.days or range(5)):
                ms = sorted(((sid, m) for sid, m in groups if m.day == day), key=lambda x: x[1].start)
                if not any(sid in scope for sid, _ in ms):
                    continue
                pairs = list(zip(ms, ms[1:]))
                if b.kind == "between_each" and any(y.start - x.end < b.minutes and (xs in scope or ys in scope) for (xs, x), (ys, y) in pairs):
                    add(f"break:{k}", None, f"{label}: a break shorter than {b.minutes} min on {DAY_EN[day]}")
                if b.kind == "one_block" and len(ms) > 1 and max((y.start - x.end for (_, x), (_, y) in pairs), default=0) < b.minutes:
                    add(f"break:{k}", None, f"{label}: no free block of {b.minutes} min on {DAY_EN[day]}")
    return violations


def _break_groups(data, rules, b):
    """Meetings per break owner, as (section_id, meeting) pairs."""
    sections = {s.id: s for s in data.sections}
    if b.applies_to == "professor":
        return {p: [(s.id, m) for s in data.sections if s.professor_id == p for m in s.meetings] for p in rules.professors}
    scope = set(rules.scope_sections)
    groups = {}
    for st in data.students:
        if scope & set(st.sections):
            key = tuple(sorted(st.sections))
            groups.setdefault(f"students {'|'.join(key)}", [(sid, m) for sid in key for m in sections[sid].meetings])
    return groups


def student_groups_in_scope(data, rules):
    """Distinct enrollment patterns touching the scope (used by the solver for student breaks)."""
    scope = set(rules.scope_sections)
    return sorted({tuple(sorted(st.sections)) for st in data.students if scope & set(st.sections)})


BREAK_GRID = 15


def add_break_constraints(model, rules, data, intervals_by_section, groups_by_section=None):
    """CP-SAT constraints for minimum breaks. intervals_by_section[sid] = [(present, day, start, end), ...] for every option meeting."""
    scope = set(rules.scope_sections)
    for b in rules.breaks:
        day_set = b.days or list(range(5))
        if b.applies_to == "professor":
            owners = [[s.id for s in data.sections if s.professor_id == p] for p in rules.professors]
        else:
            owners = [list(key) for key in student_groups_in_scope(data, rules)]
        for sids in owners:
            for day in day_set:
                terms = [(present, start, end) for sid in sids for present, d, start, end in intervals_by_section.get(sid, []) if d == day]
                movable = [(present, start, end) for sid in sids if sid in scope
                           for present, d, start, end in intervals_by_section.get(sid, []) if d == day]
                if len(terms) < 2 or not movable:
                    continue
                if b.kind == "between_each":
                    # Only pairs with a section in scope: meetings outside it are fixed and not this request's to fix.
                    fixed = [(start, end) for sid in sids if sid not in scope
                             for _, d, start, end in intervals_by_section.get(sid, []) if d == day]
                    model.add_no_overlap([model.new_optional_fixed_size_interval_var(day * 1440 + start, end - start + b.minutes, present, "brk")
                                          for present, start, end in movable])
                    for present, start, end in movable:
                        if any(start < fe + b.minutes and fs < end + b.minutes for fs, fe in fixed):
                            model.add(present == 0)
                else:
                    blocks = []
                    for bs in range(data.policy.open_minute, data.policy.close_minute - b.minutes + 1, BREAK_GRID):
                        be = bs + b.minutes
                        before = [p for p, s, e in terms if e <= bs]
                        after = [p for p, s, e in terms if s >= be]
                        if not before or not after:
                            continue
                        y = model.new_bool_var("block")
                        for p, s, e in terms:
                            if s < be and bs < e:
                                model.add_bool_or([y.Not(), p.Not()])
                        model.add_bool_or([y.Not(), *before])
                        model.add_bool_or([y.Not(), *after])
                        blocks.append(y)
                    few = model.new_bool_var("few")
                    model.add(sum(p for p, s, e in terms) <= 1).only_enforce_if(few)
                    # Binds only on days where a section in scope meets (a fully fixed day is left as it is).
                    touched = model.new_bool_var("touched")
                    model.add_max_equality(touched, [p for p, _, _ in movable])
                    model.add_bool_or([few, *blocks]).only_enforce_if(touched)


def optimize_with_rules(data, rules: RuleSet, seconds=10):
    """Scheduling tool with rules. When the rules cannot be met, find which single rules block them (spec §18.4)."""
    from .solver import optimize
    from .analysis import validate, compare
    if not check_rules(data, data, rules) and not validate(data):
        # The official timetable already meets every rule (must_change/must_change_room fail on an unchanged
        # timetable, so explicit move requests never stop here). A rule request is not an optimization request.
        return dict(status="OPTIMAL", already_satisfied=True, runtime=0, candidates=0, rule_violations=[],
                    comparison=compare(data, data), rule_set=rules.model_dump(), rule_items=rule_items(rules),
                    message="The current timetable already meets these rules; no change is needed.")
    result = optimize(data, rules.max_changes, seconds, rules=rules)
    result["rule_set"] = rules.model_dump()
    result["rule_items"] = rule_items(rules)
    if result["status"] == "INFEASIBLE":
        blocking = []
        for item in result["rule_items"]:
            relaxed = optimize(data, rules.max_changes, min(seconds, 5), rules=without(rules, item["id"]))
            if relaxed["status"] in {"OPTIMAL", "FEASIBLE"}:
                blocking.append(item)
        result["diagnosis"] = dict(
            blocking_rules=blocking,
            en=("Each listed rule, on its own, cannot be met without a clash for students, the professor or a room, or a limit you set."
                if blocking else "The rules conflict only in combination, or with the timetable's hard constraints."),
            ar=("كل قاعدة مذكورة لا يمكن تحقيقها دون تعارض للطلاب أو الأستاذ أو القاعة، أو دون تجاوز حدّ حددته."
                if blocking else "القواعد تتعارض مجتمعةً، أو مع القيود الإلزامية للجدول."))
    elif result["status"] == "UNKNOWN":
        result["diagnosis"] = dict(blocking_rules=[], en="No schedule was found within the time limit. This does not prove the rules are impossible.",
                                   ar="لم يُعثر على جدول ضمن المهلة المحددة، وهذا لا يثبت استحالة القواعد.")
    return result
