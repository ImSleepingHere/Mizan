"""Large-neighbourhood search: same objective as the full model, staged search."""
import random
import pytest
from ortools.sat.python import cp_model
from backend import lns
from backend.analysis import validate
from backend.fixtures import generate, generate_faculty
from backend.models import Semester
from backend.solver import optimize, options_for, bounded_options

STRATEGIES = [None, "time_saved", "fewest_changes", "balanced"]


def options(data):
    result = {}
    for s in data.sections:
        opts = bounded_options(s, options_for(data, s))
        result[s.id] = opts if s in opts else [s] + opts
    return result


@pytest.mark.parametrize("strategy", STRATEGIES)
def test_score_equals_the_full_model_objective(strategy):
    data = generate(groups=2, per_group=6)
    result = optimize(data, 5, 5, strategy=strategy)
    assert result["status"] == "OPTIMAL"
    placement = {s.id: s for s in Semester.model_validate(result["candidate"]).sections}
    assert lns.Context(data, 5, strategy).score(placement) == pytest.approx(result["objective"], rel=1e-15)


@pytest.fixture(scope="module")
def faculty():
    return generate_faculty()


@pytest.fixture(scope="module")
def improved(faculty):
    result = optimize(faculty, max_changes=5, seconds=5)
    return {s.id: s for s in Semester.model_validate(result["candidate"]).sections}


@pytest.mark.parametrize("strategy", STRATEGIES)
def test_round_model_scores_the_hinted_timetable_exactly(faculty, improved, monkeypatch, strategy):
    # With every variable pinned to its hint, the compact round model must value the
    # current timetable exactly as score() does: constants folded, nothing lost.
    seen = {}
    solve = cp_model.CpSolver.solve
    def pinned(self, model, *args, **kwargs):
        self.parameters.fix_variables_to_their_hinted_value = True
        status = solve(self, model, *args, **kwargs)
        seen.update(status=status, objective=self.objective_value)
        return status
    monkeypatch.setattr(cp_model.CpSolver, "solve", pinned)
    ctx, opts = lns.Context(faculty, 5, strategy), options(faculty)
    placement = dict(improved)          # five sections already moved by a real search
    moved = {sid for sid in placement if placement[sid] != ctx.original[sid]}
    assert moved
    free = set(random.Random(7).sample(sorted(ctx.original), 24)) | set(sorted(moved)[:2])
    lns._round(ctx, opts, placement, free, strategy, False, 5, 1)
    assert seen["status"] == cp_model.OPTIMAL
    assert seen["objective"] == pytest.approx(ctx.score(placement, strategy), rel=1e-15)


def test_mixed_roster_semester_gets_a_validated_plan_in_ten_seconds(faculty):
    result = optimize(faculty, max_changes=5, seconds=10)
    assert result["status"] == "FEASIBLE" and result["rounds"] > 0
    assert "Large-neighbourhood search" in result["search_scope"]
    candidate = Semester.model_validate(result["candidate"])
    assert validate(candidate) == []
    assert 0 < len(result["comparison"]["changes"]) <= 5
    assert result["comparison"]["recovered_hours"] > 0
    assert result["objective"] < lns.Context(faculty, 5, None).score({s.id: s for s in faculty.sections})


def test_strategies_reach_their_minimum_saving_on_mixed_rosters(faculty):
    for strategy in ["time_saved", "fewest_changes"]:
        result = optimize(faculty, max_changes=5, seconds=10, strategy=strategy)
        assert result["status"] == "FEASIBLE", strategy
        saved = result["comparison"]["recovered_hours"]*60
        assert saved >= result["minimum_saved_minutes"]
        assert len(result["comparison"]["changes"]) <= 5


def test_small_cohort_semesters_keep_the_full_model(monkeypatch):
    monkeypatch.setattr(lns, "search", lambda *a, **k: pytest.fail("baseline-sized runs must not use LNS"))
    assert optimize(generate(groups=2, per_group=6), 5, 5)["status"] == "OPTIMAL"
