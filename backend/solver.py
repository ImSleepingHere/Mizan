"""CP-SAT candidate search. Independent validation is mandatory before use."""
from collections import defaultdict
from time import perf_counter
from math import lcm, ceil
from ortools.sat.python import cp_model
from .models import Window, Section
from .analysis import available, overlaps, indexes, validate, compare, eligible_students, student_metrics


def options_for(data, section, room_limit=3):
    courses, profs, rooms = indexes(data)
    course, prof = courses[section.course_id], profs[section.professor_id]
    eligible_rooms = [r for r in data.rooms if r.type == course.room_type and r.capacity >= section.capacity]
    eligible_rooms.sort(key=lambda r:(r.id != section.room_id, r.id))
    options = []
    first = min(m.start for m in section.meetings)
    starts = sorted(set(data.policy.allowed_starts + [first]))
    for day_shift in range(-4, 5):
        if any(not 0 <= m.day+day_shift <= 4 for m in section.meetings):
            continue
        for start in starts:
            minutes_shift = start-first
            raw = [dict(day=m.day+day_shift, start=m.start+minutes_shift, end=m.end+minutes_shift) for m in section.meetings]
            if any(m["start"]<data.policy.open_minute or m["end"]>data.policy.close_minute for m in raw):
                continue
            meetings = [Window(**m) for m in raw]
            if any(not available(m,prof.availability) or any(overlaps(m,b) for b in data.policy.blocked) for m in meetings):
                continue
            for room in eligible_rooms[:room_limit]:
                if all(available(m,room.availability) for m in meetings):
                    options.append(section.model_copy(update=dict(room_id=room.id, meetings=meetings)))
    return options


def optimize(data, max_changes=5, seconds=10, movable=None, rules=None, strategy=None):
    """movable: optional set of section IDs that may change (e.g. a professor's own sections); all others stay fixed.
    rules: optional RuleSet (spec §18.4) applied as hard constraints to its scope; candidates are re-checked independently."""
    from .rules import option_ok, split_options, needs_split, is_split, add_break_constraints, check_rules, split_reasons
    started = perf_counter()
    if rules is not None:
        movable = set(rules.scope_sections)
        max_changes = min(max_changes, rules.max_changes)
    intervals_by_section, split_vars = defaultdict(list), []
    issues = validate(data)
    if issues:
        return dict(status="INVALID_BASELINE", message="Resolve hard violations before optimization", issues=issues[:30])
    if strategy not in {None, "time_saved", "fewest_changes", "balanced"}:
        raise ValueError("Unknown optimization strategy")
    model = cp_model.CpModel()
    resource_intervals = defaultdict(list)
    choices, modified, option_counts = {}, [], []
    # Group identical enrollment patterns; all student weights remain exact.
    patterns = defaultdict(int)
    for student in data.students:
        patterns[tuple(sorted(student.sections))] += 1
    memberships = defaultdict(list)
    for group, signature in enumerate(patterns):
        for sid in signature:
            memberships[sid].append(group)
    day_terms = defaultdict(list)
    for section in data.sections:
        if movable is not None and section.id not in movable:
            opts = [section]
        elif rules is not None:
            # Rule-scoped section: every generated option that satisfies the rules, split times only where a rule needs them.
            opts = options_for(data, section, room_limit=len(data.rooms) if section.id in rules.must_change_room else 3)
            if needs_split(rules, section):
                opts += split_options(data, section)
            unique = []
            for o in opts:
                if o not in unique and option_ok(rules, section, o):
                    unique.append(o)
            unique.sort(key=lambda o: (o != section, is_split(section, o), o.room_id != section.room_id,
                                       sum(abs(a.start - b.start) + 1440 * (a.day != b.day) for a, b in zip(o.meetings, section.meetings))))
            opts = unique[:60]
            if not opts:
                return dict(status="INFEASIBLE", runtime=round(perf_counter()-started, 3), blocked_section=section.id,
                            message=f"No placement of {section.id} satisfies the rules", candidates=0)
        else:
            opts = options_for(data,section)
        # Bounded neighborhood keeps the interactive run small. Preserve every approved
        # start on the current days/room, plus a few day/room alternatives and baseline.
        current_days=[m.day for m in section.meetings]
        opts.sort(key=lambda o:(o != section, [m.day for m in o.meetings] != current_days,
                               o.room_id != section.room_id, abs(o.meetings[0].start-section.meetings[0].start)))
        primary=[o for o in opts if [m.day for m in o.meetings]==current_days and o.room_id==section.room_id]
        room_extra=next((o for o in opts if [m.day for m in o.meetings]==current_days and o.room_id!=section.room_id),None)
        day_extras=[]
        seen_days=set()
        for o in opts:
            pattern=tuple(m.day for m in o.meetings)
            if list(pattern)!=current_days and pattern not in seen_days and o.room_id==section.room_id:
                day_extras.append(o)
                seen_days.add(pattern)
        if not (rules is not None and section.id in movable):
            opts=primary+([room_extra] if room_extra else [])+day_extras[:2]
        option_counts.append(len(opts))
        if not opts:
            return dict(status="INFEASIBLE", message="No feasible option in the configured candidate neighborhood")
        variables = [model.new_bool_var(f"{section.id}_{i}") for i in range(len(opts))]
        model.add_exactly_one(variables)
        choices[section.id] = (opts,variables)
        moved = model.new_bool_var(f"moved_{section.id}")
        model.add(moved == sum(v for o,v in zip(opts,variables) if o != section))
        modified.append(moved)
        for oi,(opt,present) in enumerate(zip(opts,variables)):
            model.add_hint(present, int(opt==section))
            if is_split(section, opt):
                split_vars.append(present)
            for mi,m in enumerate(opt.meetings):
                intervals_by_section[section.id].append((present, m.day, m.start, m.end))
                absolute = m.day*1440+m.start
                interval = model.new_optional_fixed_size_interval_var(absolute,m.end-m.start,present,f"iv_{section.id}_{oi}_{mi}")
                resource_intervals[("room",opt.room_id)].append(interval)
                resource_intervals[("prof",opt.professor_id)].append(interval)
                for group in memberships[section.id]:
                    resource_intervals[("group",group)].append(interval)
                    day_terms[(group,m.day)].append((present,m.start,m.end))
    for intervals in resource_intervals.values():
        model.add_no_overlap(intervals)
    model.add(sum(modified) <= max_changes)
    if rules is not None:
        add_break_constraints(model, rules, data, intervals_by_section)
    gaps, days, irregular = [], [], []
    for group,(signature,count) in enumerate(patterns.items()):
        group_gaps, group_days = [], []
        for day in range(5):
            terms = day_terms[(group,day)]
            if not terms:
                continue
            starts, ends, active = [], [], model.new_bool_var(f"active_{group}_{day}")
            for k,(present,start,end) in enumerate(terms):
                # Unselected candidates cannot affect extrema.
                starts.append(1440+(start-1440)*present)
                ends.append(end*present)
            model.add_max_equality(active,[t[0] for t in terms])
            earliest=model.new_int_var(0,1440,f"early_{group}_{day}")
            latest=model.new_int_var(0,1440,f"late_{group}_{day}")
            model.add_min_equality(earliest,starts)
            model.add_max_equality(latest,ends)
            gap=model.new_int_var(0,1440,f"gap_{group}_{day}")
            model.add(gap == latest-earliest+1440*(1-active)-sum((end-start)*present for present,start,end in terms))
            group_gaps.append(gap)
            group_days.append(active)
        total=model.new_int_var(0,7200,f"total_{group}")
        model.add(total==sum(group_gaps))
        gaps.append((total,count))
        days.append((sum(group_days),count))
    worst=model.new_int_var(0,7200,"worst_gap")
    model.add_max_equality(worst,[v for v,c in gaps] or [0])
    weights=data.policy.weights
    population=max(1,len(data.students))
    # Exact common integer scale preserves the configured weight ratios.
    meeting_count=max(1,sum(len(s.meetings) for s in data.sections))
    scale=lcm(population*1200,population*5,1200,max(1,len(data.sections)),meeting_count)
    gap_coef=scale//(population*1200)
    day_coef=scale//(population*5)
    change_coef=scale//max(1,len(data.sections))
    for section in data.sections:
        opts, variables=choices[section.id]
        irregular.extend(sum(m.start%30 != 0 or m.end%30 != 0 for m in o.meetings)*v for o,v in zip(opts,variables))
    objective=(weights["gaps"]*gap_coef*sum(v*c for v,c in gaps)
               +weights["days"]*day_coef*sum(v*c for v,c in days)
               +weights["fairness"]*(scale//1200)*worst
               +weights["changes"]*change_coef*sum(modified)
               +weights["simplicity"]*(scale//meeting_count)*sum(irregular)
               # Split meeting times are allowed only by rules, and discouraged (twice an irregular meeting).
               +2*weights["simplicity"]*(scale//meeting_count)*sum(split_vars))
    if strategy is not None:
        gap_total = sum(v*c for v,c in gaps)
        day_total = sum(v*c for v,c in days)
        baseline_gap = sum(s["gap_minutes"] for s in student_metrics(data))
        # Every alternative is a genuine improvement in aggregate waiting time.
        # A zero-gap timetable needs no gap-reduction proposal.
        minimum_saved = max(1, ceil(baseline_gap * .01))
        model.add(gap_total <= baseline_gap - minimum_saved)
        if strategy == "fewest_changes":
            # Lexicographic: one fewer moved section beats ANY possible gap gain.
            objective = sum(modified)*(7200*population+1) + gap_total
        elif strategy == "time_saved":
            # Lexicographic: minimize gaps, then campus days, then disruption.
            objective = (gap_total*(5*population+1)+day_total)*(len(data.sections)+1)+sum(modified)
        else:
            # Exact worst-decile sum using weighted enrollment patterns (CVaR).
            # The threshold formulation also works when the decile splits a group.
            tail_count = max(1, ceil(len(data.students)*.1))
            threshold = model.new_int_var(0,7200,"tail_threshold")
            excess = []
            for index,(total,count) in enumerate(gaps):
                over = model.new_int_var(0,7200,f"tail_excess_{index}")
                model.add_max_equality(over,[total-threshold,0])
                excess.append(count*over)
            tail_sum = tail_count*threshold+sum(excess)
            tail = model.new_int_var(0,tail_count*7200,"tail_sum")
            model.add(tail == tail_sum)
            squares = []
            for index,(total,count) in enumerate(gaps):
                square = model.new_int_var(0,7200*7200,f"gap_square_{index}")
                model.add_multiplication_equality(square,[total,total])
                squares.append(count*square)
            # Worst-decile sum first, then squared gaps favor spreading relief
            # instead of improving just a few identical cohorts. Include overall
            # gaps and disruption as small secondary costs. Bounded below int64
            # for the supported 10,000-student / 1,000-section import limits.
            secondary_bound = population*(7200*7200+60*7200)+len(data.sections)
            objective = tail*(secondary_bound+1)+sum(squares)+60*gap_total+sum(modified)
    model.minimize(objective)
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=seconds
    solver.parameters.num_search_workers=4
    solver.parameters.random_seed=data.seed
    status=solver.solve(model)
    report=dict(status=solver.status_name(status), runtime=round(perf_counter()-started,3),
                search_scope="Bounded candidate neighborhood: all approved starts on current days/room plus three alternatives per section; meeting spacing preserved and faculty fixed. Optimal applies only to this neighborhood.",
                invariant_objectives=["Teaching-load balance and total room utilization are constant in this search because teaching assignments and instructional minutes are fixed."],
                candidates=sum(option_counts), objective_version="1.0", weights=weights)
    if strategy is not None:
        report.update(strategy=strategy, minimum_saved_minutes=minimum_saved,
                      objective_version="alternatives-1.0")
    if status not in [cp_model.OPTIMAL,cp_model.FEASIBLE]:
        return dict(**report,message="No feasible improvement established; official timetable retained")
    candidate=data.model_copy(deep=True)
    candidate.sections=[next(o for o,v in zip(*choices[s.id]) if solver.value(v)) for s in data.sections]
    candidate_issues=validate(candidate)
    if candidate_issues:
        return dict(**report, validation_failed=True, message="Independent validation rejected the candidate",issues=candidate_issues)
    if rules is not None:
        report["rule_violations"]=check_rules(data,candidate,rules)
        if report["rule_violations"]:
            return dict(**report, validation_failed=True, message="Independent rule check rejected the candidate")
        before={s.id:s for s in data.sections}
        report["split_times"]=[dict(section_id=s.id,reasons=split_reasons(rules,before[s.id],s)) for s in candidate.sections if is_split(before[s.id],s)]
    diff=compare(data,candidate)
    return dict(**report,objective=solver.objective_value,best_bound=solver.best_objective_bound,
                comparison=diff,candidate=candidate.model_dump(),message="Candidate independently validated" if diff["changes"] else "No change recommended")


def placement(data, course_id, capacity=80):
    courses,profs,rooms=indexes(data)
    course=courses[course_id]
    eligible=eligible_students(data,course_id)
    enrolled_sections={s.id:s for s in data.sections}
    loads={p.id:sum(m.end-m.start for s in data.sections if s.professor_id==p.id for m in s.meetings) for p in data.professors}
    options=[]
    # Use approved consecutive weekday patterns; every returned option is checked against resources.
    for first_day in range(6-course.meetings_per_week):
        for start in data.policy.allowed_starts:
            if start+course.duration>data.policy.close_minute:
                continue
            meetings=[Window(day=first_day+j,start=start,end=start+course.duration) for j in range(course.meetings_per_week)]
            if any(any(overlaps(m,b) for b in data.policy.blocked) for m in meetings):
                continue
            professor=next((p for p in data.professors if course.competency in p.competencies
                            and loads[p.id]+course.duration*course.meetings_per_week<=p.contracted_minutes
                            and all(available(m,p.availability) for m in meetings)
                            and not any(overlaps(m,existing) for s in data.sections if s.professor_id==p.id for existing in s.meetings for m in meetings)),None)
            room=next((r for r in data.rooms if r.capacity>=capacity and r.type==course.room_type
                       and all(available(m,r.availability) for m in meetings)
                       and not any(overlaps(m,existing) for s in data.sections if s.room_id==r.id for existing in s.meetings for m in meetings)),None)
            if not professor or not room:
                continue
            compatible=[]
            added_gaps=extra_days=0
            for student in eligible:
                current=[m for sid in student.sections for m in enrolled_sections[sid].meetings]
                if any(overlaps(a,b) for a in current for b in meetings):
                    continue
                def total_gap(ms):
                    byday=defaultdict(list)
                    for m in ms: byday[m.day].append(m)
                    return sum(max(x.end for x in v)-min(x.start for x in v)-sum(x.end-x.start for x in v) for v in byday.values())
                delta=total_gap(current+meetings)-total_gap(current)
                additional=len({m.day for m in meetings}-{m.day for m in current})
                compatible.append(dict(student_id=student.id,gap_delta=delta,extra_days=additional))
                added_gaps+=delta
                extra_days+=additional
            options.append(dict(meetings=[m.model_dump() for m in meetings], professor_id=professor.id, room_id=room.id,
                                capacity=capacity,eligible_count=len(eligible),compatible_count=len(compatible),
                                seats_available=min(capacity,len(compatible)),gap_delta_hours=round(added_gaps/60,2),
                                extra_campus_days=extra_days,compatible_students=compatible))
    options.sort(key=lambda o:(-min(o["compatible_count"],capacity),o["extra_campus_days"],o["gap_delta_hours"]))
    return dict(course_id=course_id,eligible_count=len(eligible),options=options[:15],
                note="Gap totals cover all compatible students, not a selected enrollment roster. Seat allocation remains a staff decision.")


def _unseated(demand,covered_sections):
    """Students left without a seat when only the covered sections run, demand split evenly across the required sections."""
    wanting=len(set(demand.students))
    per_section=-(-wanting//max(1,demand.sections))
    return max(0,wanting-covered_sections*per_section)


def workforce(data):
    courses,profs,rooms=indexes(data)
    load={p.id:sum(m.end-m.start for s in data.sections if s.professor_id==p.id for m in s.meetings) for p in data.professors}
    signals=[]
    for demand in data.demands:
        course=courses[demand.course_id]
        qualified=[p for p in data.professors if course.competency in p.competencies]
        unit=course.duration*course.meetings_per_week
        # Integer section capacity bound; independent of time placement.
        residual=sum(max(0,p.contracted_minutes-load[p.id])//unit for p in qualified)
        absolute=sum(p.contracted_minutes//unit for p in qualified)
        unavoidable=max(0,demand.sections-absolute)
        current_short=max(0,demand.sections-residual)
        redeploy=[]
        for s in data.sections:
            if s.professor_id not in {p.id for p in qualified}:
                continue
            c=courses[s.course_id]
            for p in data.professors:
                minutes=sum(m.end-m.start for m in s.meetings)
                if p.id==s.professor_id or c.competency not in p.competencies or load[p.id]+minutes>p.contracted_minutes:
                    continue
                candidate=data.model_copy(deep=True)
                next(x for x in candidate.sections if x.id==s.id).professor_id=p.id
                if not validate(candidate):
                    redeploy.append(dict(section_id=s.id,from_professor=s.professor_id,to_professor=p.id,freed_minutes=minutes))
                    break
        signals.append(dict(demand_id=demand.id,course_id=course.id,department=course.department,competency=course.competency,
                            required_sections=demand.sections,current_coverage_sections=min(residual,demand.sections),
                            minimum_unservable_sections=unavoidable,current_capacity_gap_sections=current_short,
                            students_at_risk=_unseated(demand,min(residual,demand.sections)),students_demanding=len(set(demand.students)),required_minutes=demand.sections*unit,
                            qualified_instructors=[dict(id=p.id,name=p.name,contracted_minutes=p.contracted_minutes,assigned_minutes=load[p.id]) for p in qualified],
                            status="PROVEN_CAPACITY_SHORTFALL" if unavoidable else "REDEPLOYMENT_REVIEW" if current_short else "CAPACITY_AVAILABLE",
                            binding_constraint="Qualified contracted teaching capacity" if unavoidable else "Detailed time placement requires review",
                            evidence=f"{demand.sections} required sections; even all qualified contracts cover at most {absolute} sections of {unit} minutes.",
                            internal_options=redeploy,additional_minutes_needed=unavoidable*unit,
                            note="Internal options are individually validated, not a jointly approved plan. Capacity availability does not prove timetable feasibility."))
    return dict(signals=signals,workloads=[dict(id=p.id,name=p.name,department=p.department,minutes=load[p.id],contracted_minutes=p.contracted_minutes) for p in data.professors])


def common_slots(data, section_ids, duration, days=None, same_time_for_all=False, merge=False,
                 earliest=None, latest_end=None, grid=15, limit=10):
    """Common free-slot finder (spec §18.5): ranked weekly slots for the students of the given sections.

    For each candidate slot: how many of those students are busy, whether every needed professor is free,
    and a free room large enough (one room for a merge, otherwise one room per section when all sections meet
    at the same time). Counts only; no student identities. A weekly slot repeats in every teaching week."""
    courses, profs, rooms = indexes(data)
    sections = {s.id: s for s in data.sections}
    group = [sections[s] for s in section_ids]
    members = {st.id: st for st in data.students if set(section_ids) & set(st.sections)}
    exclude = set(section_ids) if merge else set()  # a merged lecture replaces the merged sections' own meetings
    busy = {sid: [m for m in st.sections if m not in exclude] for sid, st in members.items()}
    busy = {sid: [mt for x in ids for mt in sections[x].meetings] for sid, ids in busy.items()}
    teachers = {group[0].professor_id} if merge else {s.professor_id for s in group}
    teacher_busy = [m for s in data.sections if s.professor_id in teachers and s.id not in exclude for m in s.meetings]
    room_busy = defaultdict(list)
    for s in data.sections:
        if s.id not in exclude:
            room_busy[s.room_id].extend(s.meetings)
    size = {s.id: sum(s.id in st.sections for st in data.students) for s in group}
    room_type = courses[group[0].course_id].room_type
    def free_rooms(w, need):
        """Rooms for the slot: one big room (merge / single section) or one room per section."""
        cands = sorted((r for r in data.rooms if r.type == room_type and available(w, r.availability)
                        and not any(overlaps(w, m) for m in room_busy[r.id])), key=lambda r: (r.capacity, r.id))
        if merge or len(group) == 1 or not same_time_for_all:
            total = sum(need.values()) if merge else max(need.values())
            room = next((r for r in cands if r.capacity >= total), None)
            return [room.id] if room else None
        chosen = []
        for sid, n in sorted(need.items(), key=lambda x: -x[1]):
            room = next((r for r in cands if r.capacity >= n and r.id not in chosen), None)
            if not room:
                return None
            chosen.append(room.id)
        return chosen
    def total_gap(ms):
        byday = defaultdict(list)
        for m in ms: byday[m.day].append(m)
        return sum(max(x.end for x in v) - min(x.start for x in v) - sum(x.end - x.start for x in v) for v in byday.values())
    results = []
    for day in (days if days else range(5)):
        for start in range(max(data.policy.open_minute, earliest or 0), data.policy.close_minute - duration + 1, grid):
            end = start + duration
            if latest_end is not None and end > latest_end:
                break
            w = Window(day=day, start=start, end=end)
            if any(overlaps(w, b) for b in data.policy.blocked):
                continue
            professor_free = all(available(w, profs[p].availability) for p in teachers) and not any(overlaps(w, m) for m in teacher_busy)
            unavailable = extra_days = gap_delta = 0
            for sid, ms in busy.items():
                if any(overlaps(w, m) for m in ms):
                    unavailable += 1
                    continue
                if day not in {m.day for m in ms}:
                    extra_days += 1
                gap_delta += total_gap(ms + [w]) - total_gap(ms)
            room_ids = free_rooms(w, size)
            results.append(dict(day=day, start=start, end=end, group_size=len(members), unavailable=unavailable,
                                available=len(members) - unavailable, professor_free=professor_free, rooms=room_ids,
                                extra_campus_days=extra_days, added_gap_hours=round(gap_delta / 60, 1)))
    results.sort(key=lambda r: (not r["professor_free"], r["rooms"] is None, r["unavailable"], r["extra_campus_days"], r["added_gap_hours"], r["day"], r["start"]))
    distinct = []  # distinct options: skip a slot that overlaps a better one on the same day
    for r in results:
        if not any(k["day"] == r["day"] and k["start"] < r["end"] and r["start"] < k["end"] for k in distinct):
            distinct.append(r)
        if len(distinct) == limit:
            break
    return dict(sections=list(section_ids), group_size=len(members), duration=duration, merge=merge, same_time_for_all=same_time_for_all,
                slots=distinct, searched=len(results),
                note="Weekly timetable: a free slot repeats every teaching week. Date-specific exceptions are not checked.")
