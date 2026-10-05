"""Large-neighbourhood search for whole-semester runs with mixed rosters.

The full CP-SAT model in `solver.optimize` tracks every distinct enrollment pattern
on every day. With mixed rosters (one pattern per student) that is ~32k variables
and ~140k intervals; presolve alone outlasts interactive time limits. Here each
round frees a small set of sections and fixes the rest, so fixed meetings become
constants: clashing options are dropped up front, untouched patterns are plain
numbers and patterns with the same free sections and fixed day profile merge.
The per-round model optimizes exactly the same objective as `solver.optimize`
(`score` mirrors it and tests check the equality); only the search is staged.
"""
from collections import defaultdict
from itertools import product
from math import ceil, lcm
from time import perf_counter
from ortools.sat.python import cp_model
from .analysis import validate, compare, student_metrics

NEIGHBOURHOOD = 24          # free sections per round at the start
MAX_NEIGHBOURHOOD = 96      # grown (x1.5) each time a size stops finding gains
MAX_COMBOS = 2000           # per free set; a larger round is skipped
ROUND_SECONDS = 3.0         # upper bound per round; small models usually prove OPTIMAL sooner


def _overlap(a, b):
    return a.day == b.day and a.start < b.end and b.start < a.end


def _clash(o, p):
    return any(_overlap(x, y) for x in o.meetings for y in p.meetings)


def _irregular(o):
    return sum(m.start % 30 != 0 or m.end % 30 != 0 for m in o.meetings)


def _pattern_stats(signature, placement):
    """(gap minutes, campus days) as the CP model counts them: span minus busy per day."""
    days = defaultdict(list)
    for sid in signature:
        for m in placement[sid].meetings:
            days[m.day].append(m)
    gap = sum(max(m.end for m in ms) - min(m.start for m in ms) - sum(m.end - m.start for m in ms) for ms in days.values())
    return gap, len(days)


class Context:
    def __init__(self, data, max_changes, strategy):
        self.data, self.max_changes, self.strategy = data, max_changes, strategy
        self.original = {s.id: s for s in data.sections}
        counts = defaultdict(int)
        for student in data.students:
            counts[tuple(sorted(student.sections))] += 1
        self.patterns = list(counts.items())
        self.members = defaultdict(list)
        for index, (signature, _) in enumerate(self.patterns):
            for sid in signature:
                self.members[sid].append(index)
        # Sections sharing students, weighted by how many students they share.
        self.shared = defaultdict(lambda: defaultdict(int))
        for signature, count in self.patterns:
            for a in signature:
                for b in signature:
                    if a != b:
                        self.shared[a][b] += count
        self.population = max(1, len(data.students))
        self.sections = max(1, len(data.sections))
        self.meeting_count = max(1, sum(len(s.meetings) for s in data.sections))
        self.scale = lcm(self.population*1200, self.population*5, 1200, self.sections, self.meeting_count)
        self.weights = data.policy.weights
        self.baseline_gap = sum(s["gap_minutes"] for s in student_metrics(data))
        self.minimum_saved = max(1, ceil(self.baseline_gap * .01))
        self.tail_count = max(1, ceil(len(data.students) * .1))

    def score(self, placement, objective=None):
        """Exact value of the CP-SAT objective of `solver.optimize` for a placement."""
        objective = objective or self.strategy
        stats = [(_pattern_stats(sig, placement), count) for sig, count in self.patterns]
        gap_total = sum(g*c for (g, _), c in stats)
        day_total = sum(d*c for (_, d), c in stats)
        moved = sum(placement[sid] != sec for sid, sec in self.original.items())
        if objective is None:
            w, scale = self.weights, self.scale
            return (w["gaps"]*(scale//(self.population*1200))*gap_total
                    + w["days"]*(scale//(self.population*5))*day_total
                    + w["fairness"]*(scale//1200)*max((g for (g, _), _c in stats), default=0)
                    + w["changes"]*(scale//self.sections)*moved
                    + w["simplicity"]*(scale//self.meeting_count)*sum(_irregular(placement[sid]) for sid in self.original))
        if objective == "fewest_changes":
            return moved*(7200*self.population+1) + gap_total
        if objective == "time_saved":
            return (gap_total*(5*self.population+1)+day_total)*(self.sections+1)+moved
        # balanced: worst-decile sum (CVaR), squared gaps, total gaps, disruption.
        values, left, tail = sorted(((g, c) for (g, _), c in stats), reverse=True), self.tail_count, 0
        for g, c in values:
            take = min(c, left)
            tail, left = tail + g*take, left - take
            if not left:
                break
        bound = self.population*(7200*7200+60*7200)+len(self.data.sections)
        return tail*(bound+1) + sum(g*g*c for (g, _), c in stats) + 60*gap_total + moved

    def gap_total(self, placement):
        return sum(_pattern_stats(sig, placement)[0]*count for sig, count in self.patterns)


def _round(ctx, options, placement, free, objective, enforce_saving, seconds, seed):
    """Exact solve over `free` with every other section fixed at `placement`."""
    fixed = [sid for sid in ctx.original if sid not in free]
    by_room, by_prof = defaultdict(list), defaultdict(list)
    for sid in fixed:
        by_room[placement[sid].room_id].append(placement[sid])
        by_prof[placement[sid].professor_id].append(placement[sid])
    model = cp_model.CpModel()
    choice = {}
    for sid in free:
        neighbours = [placement[o] for o in ctx.shared[sid] if o not in free]
        opts = [o for o in options[sid] if o == placement[sid] or not (
            any(_clash(o, f) for f in by_room[o.room_id]) or any(_clash(o, f) for f in by_prof[o.professor_id])
            or any(_clash(o, f) for f in neighbours))]
        if placement[sid] not in opts:
            opts.insert(0, placement[sid])
        variables = [model.new_bool_var(f"{sid}_{i}") for i in range(len(opts))]
        model.add_exactly_one(variables)
        for o, v in zip(opts, variables):
            model.add_hint(v, int(o == placement[sid]))
        choice[sid] = (opts, variables)
    # Clashes among free sections: shared rooms and professors, and shared students.
    resources = defaultdict(list)
    for sid in free:
        for oi, (o, v) in enumerate(zip(*choice[sid])):
            for mi, m in enumerate(o.meetings):
                iv = model.new_optional_fixed_size_interval_var(m.day*1440+m.start, m.end-m.start, v, f"iv_{sid}_{oi}_{mi}")
                resources[("room", o.room_id)].append((sid, iv))
                resources[("prof", o.professor_id)].append((sid, iv))
    for items in resources.values():
        if len({sid for sid, _ in items}) > 1:
            model.add_no_overlap([iv for _, iv in items])
    free_list = sorted(free)
    for i, a in enumerate(free_list):
        for b in free_list[i+1:]:
            if b in ctx.shared[a]:
                for oa, va in zip(*choice[a]):
                    for ob, vb in zip(*choice[b]):
                        if _clash(oa, ob):
                            model.add_bool_or([va.Not(), vb.Not()])
    # Patterns touching a free section; merge identical free sets + fixed day profiles.
    touched = {p for sid in free for p in ctx.members[sid]}
    merged = defaultdict(int)
    for index in touched:
        signature, count = ctx.patterns[index]
        fixed_meetings = tuple(sorted((m.day, m.start, m.end) for sid in signature if sid not in free
                                      for m in placement[sid].meetings))
        merged[(tuple(s for s in signature if s in free), fixed_meetings)] += count
    # One choice variable per feasible combination of a free set's options. Each
    # pattern's weekly gap and campus days are then exact table lookups, so the
    # objective is linear in 0/1 variables (no min/max per day to relax).
    combos = {}
    for free_sig in {k[0] for k in merged}:
        if len(free_sig) == 1:
            sid = free_sig[0]
            combos[free_sig] = [((o,), v) for o, v in zip(*choice[sid])]
            continue
        lists = [list(zip(*choice[sid])) for sid in free_sig]
        rows = []
        for pick in product(*lists):
            opts_ = [o for o, _ in pick]
            if any(_clash(a, b) for x, a in enumerate(opts_) for b in opts_[x+1:]):
                continue
            rows.append(pick)
        if len(rows) > MAX_COMBOS:
            return None, None, 0
        ys = [model.new_bool_var(f"combo_{len(combos)}_{r}") for r in range(len(rows))]
        model.add_exactly_one(ys)
        for x, sid in enumerate(free_sig):
            for o, v in zip(*choice[sid]):
                model.add(sum(y for y, pick in zip(ys, rows) if pick[x][0] == o) == v)
        for y, pick in zip(ys, rows):
            model.add_hint(y, int(all(o == placement[sid] for (o, _), sid in zip(pick, free_sig))))
        combos[free_sig] = [(tuple(o for o, _ in pick), y) for pick, y in zip(rows, ys)]

    def week(fixed_meetings, opts_):
        days = defaultdict(list)
        for d, a, b in fixed_meetings:
            days[d].append((a, b))
        for o in opts_:
            for m in o.meetings:
                days[m.day].append((m.start, m.end))
        return sum(max(b for _, b in ms)-min(a for a, _ in ms)-sum(b-a for a, b in ms) for ms in days.values()), len(days)

    groups = []   # (count, [(gap, days, var)], current gap)
    for (free_sig, fixed_meetings), count in merged.items():
        table = []
        for opts_, var in combos[free_sig]:
            g, dcount = week(fixed_meetings, opts_)
            table.append((g, dcount, var))
        current = week(fixed_meetings, [placement[sid] for sid in free_sig])[0]
        groups.append((count, table, current))
    untouched = [ctx.patterns[i] for i in range(len(ctx.patterns)) if i not in touched]
    const_stats = [(_pattern_stats(sig, placement), count) for sig, count in untouched]
    const_gap = sum(g*c for (g, _), c in const_stats)
    const_days = sum(d*c for (_, d), c in const_stats)
    totals = [sum(g*v for g, _, v in table) for _, table, _ in groups]
    gap_total = sum(c*g*v for c, table, _ in groups for g, _, v in table) + const_gap
    day_total = sum(c*d*v for c, table, _ in groups for _, d, v in table) + const_days
    moved = [model.new_bool_var(f"moved_{sid}") for sid in free_list]
    for sid, mv in zip(free_list, moved):
        model.add(mv == sum(v for o, v in zip(*choice[sid]) if o != ctx.original[sid]))
        model.add_hint(mv, int(placement[sid] != ctx.original[sid]))
    moved_total = sum(moved) + sum(placement[sid] != ctx.original[sid] for sid in fixed)
    model.add(moved_total <= ctx.max_changes)
    if enforce_saving:
        model.add(gap_total <= ctx.baseline_gap - ctx.minimum_saved)
    const_worst = max((g for (g, _), _c in const_stats), default=0)
    if objective is None:
        w, scale = ctx.weights, ctx.scale
        # Minimized with a positive weight, so worst settles on the true maximum.
        worst = model.new_int_var(const_worst, 7200, "worst")
        for t in totals:
            model.add(worst >= t)
        model.add_hint(worst, max([cur for _, _, cur in groups] + [const_worst]))
        irregular = (sum(_irregular(o)*v for sid in free_list for o, v in zip(*choice[sid]))
                     + sum(_irregular(placement[sid]) for sid in fixed))
        expression = (w["gaps"]*(scale//(ctx.population*1200))*gap_total
                      + w["days"]*(scale//(ctx.population*5))*day_total
                      + w["fairness"]*(scale//1200)*worst
                      + w["changes"]*(scale//ctx.sections)*moved_total
                      + w["simplicity"]*(scale//ctx.meeting_count)*irregular)
    elif objective == "fewest_changes":
        expression = moved_total*(7200*ctx.population+1) + gap_total
    elif objective == "time_saved":
        expression = (gap_total*(5*ctx.population+1)+day_total)*(ctx.sections+1)+moved_total
    else:
        # CVaR: tail_count*threshold + sum count*max(total-threshold, 0); excess
        # variables are minimized, so ">=" constraints reach the max exactly.
        const_hist = defaultdict(int)
        for (g, _), c in const_stats:
            const_hist[g] += c
        # Hint the optimal threshold for the current timetable: its tail_count-th largest gap.
        ranked, left, theta = sorted([(cur, c) for c, _, cur in groups] + list(const_hist.items()), reverse=True), ctx.tail_count, 0
        for value, c in ranked:
            theta, left = value, left - c
            if left <= 0:
                break
        threshold = model.new_int_var(0, 7200, "tail_threshold")
        model.add_hint(threshold, theta)
        excess = []
        for index, ((c, _, cur), t) in enumerate(zip(groups, totals)):
            over = model.new_int_var(0, 7200, f"over_{index}")
            model.add(over >= t - threshold)
            model.add_hint(over, max(cur - theta, 0))
            excess.append(c*over)
        for index, (g, c) in enumerate(const_hist.items()):
            over = model.new_int_var(0, 7200, f"const_over_{index}")
            model.add(over >= g - threshold)
            model.add_hint(over, max(g - theta, 0))
            excess.append(c*over)
        tail = ctx.tail_count*threshold + sum(excess)
        squares = sum(c*g*g*v for c, table, _ in groups for g, _, v in table)
        bound = ctx.population*(7200*7200+60*7200)+len(ctx.data.sections)
        expression = (tail*(bound+1) + squares + sum(g*g*c for (g, _), c in const_stats)
                      + 60*gap_total + moved_total)
    model.minimize(expression)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = max(.1, seconds)
    solver.parameters.num_search_workers = 4
    solver.parameters.random_seed = seed
    # Probing took ~1.6 s even on a 48-decision round and left no time to search.
    solver.parameters.cp_model_probing_level = 0
    status = solver.solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None, status, sum(len(opts) for opts, _ in choice.values())
    result = dict(placement)
    for sid in free:
        result[sid] = next(o for o, v in zip(*choice[sid]) if solver.value(v))
    return result, status, sum(len(opts) for opts, _ in choice.values())


def _potentials(ctx, options, placement):
    """Best single-move reduction in student gap minutes per section (others fixed)."""
    gains = {}
    for sid, opts in options.items():
        others_room = [placement[o] for o in ctx.original if o != sid]
        neighbours = [placement[o] for o in ctx.shared[sid]]
        base = sum(_pattern_stats(ctx.patterns[p][0], placement)[0]*ctx.patterns[p][1] for p in ctx.members[sid])
        best = 0
        for o in opts:
            if o == placement[sid] or any(_clash(o, f) for f in neighbours) or any(
                    (f.room_id == o.room_id or f.professor_id == o.professor_id) and _clash(o, f) for f in others_room):
                continue
            trial = dict(placement)
            trial[sid] = o
            new = sum(_pattern_stats(ctx.patterns[p][0], trial)[0]*ctx.patterns[p][1] for p in ctx.members[sid])
            best = max(best, base-new)
        gains[sid] = best
    return gains


def search(data, max_changes, seconds, strategy, options, started, seed):
    ctx = Context(data, max_changes, strategy)
    deadline = started + seconds
    placement = dict(ctx.original)
    # Strategies require a minimum saving the official timetable lacks: reach it first
    # by minimizing gaps, then optimize the strategy's own objective under that floor.
    phase = "reach" if strategy is not None else "optimize"
    current = ctx.score(placement, "time_saved" if phase == "reach" else strategy)
    rounds = proven = since_improvement = 0
    gains = _potentials(ctx, options, placement)
    order = sorted(ctx.original, key=lambda s: (-gains[s], s))
    cursor, size = 0, NEIGHBOURHOOD
    while perf_counter() < deadline - .2:
        seed_sid = order[cursor % len(order)]
        cursor += 1
        free = {seed_sid} | {sid for sid in ctx.original if placement[sid] != ctx.original[sid]}
        for sid, _ in sorted(ctx.shared[seed_sid].items(), key=lambda x: (-x[1], x[0])):
            if len(free) >= size // 2:
                break
            free.add(sid)
        for sid in order:
            if len(free) >= size:
                break
            free.add(sid)
        objective = "time_saved" if phase == "reach" else strategy
        result, status, _ = _round(ctx, options, placement, free, objective, phase == "optimize" and strategy is not None,
                                   min(ROUND_SECONDS, deadline - perf_counter()), seed + rounds)
        rounds += 1
        proven += status == cp_model.OPTIMAL
        if result is not None and not validate(_semester(data, result)):
            value = ctx.score(result, objective)
            if value < current:
                placement, current, since_improvement = result, value, 0
                gains = _potentials(ctx, options, placement)
                order = sorted(ctx.original, key=lambda s: (-gains[s], s))
                cursor = 0
            else:
                since_improvement += 1
        else:
            since_improvement += 1
        if phase == "reach" and ctx.gap_total(placement) <= ctx.baseline_gap - ctx.minimum_saved:
            phase, current, since_improvement, cursor = "optimize", ctx.score(placement, strategy), 0, 0
            continue
        if since_improvement >= len(order):
            # Every seed tried since the last gain: local optimum for this size.
            if size >= min(MAX_NEIGHBOURHOOD, len(order)):
                break
            size, since_improvement, cursor = min(MAX_NEIGHBOURHOOD, len(order), size*3//2), 0, 0
    report = dict(runtime=round(perf_counter()-started, 3), rounds=rounds,
                  search_scope=("Large-neighbourhood search over the bounded candidate neighborhood: repeated exact solves of up to "
                                f"{size} sections with all others fixed ({rounds} rounds). Faculty fixed; not proven optimal."),
                  invariant_objectives=["Teaching-load balance and total room utilization are constant in this search because teaching assignments and instructional minutes are fixed."],
                  candidates=sum(len(o) for o in options.values()), objective_version="1.0" if strategy is None else "alternatives-1.0",
                  weights=data.policy.weights)
    if strategy is not None:
        report.update(strategy=strategy, minimum_saved_minutes=ctx.minimum_saved)
    if not rounds or phase == "reach":
        # No round ran, or a strategy never reached its minimum saving.
        return dict(status="UNKNOWN", **report,
                    message="Time limit reached before any plan was confirmed; official timetable retained. Try a longer search or a smaller scope.")
    candidate = _semester(data, placement)
    issues = validate(candidate)
    if issues:
        return dict(status="FEASIBLE", **report, validation_failed=True, message="Independent validation rejected the candidate", issues=issues)
    diff = compare(data, candidate)
    return dict(status="FEASIBLE", **report, objective=ctx.score(placement), comparison=diff, candidate=candidate.model_dump(),
                message="Candidate independently validated" if diff["changes"]
                else "No improvement found within the time limit; official timetable retained. A longer search may find one.")


def _semester(data, placement):
    candidate = data.model_copy(deep=True)
    candidate.sections = [placement[s.id] for s in data.sections]
    return candidate
