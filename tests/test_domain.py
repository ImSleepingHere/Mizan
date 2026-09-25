import pytest
from backend.fixtures import generate
from backend.models import Window,Semester
from backend.analysis import validate,metrics,overlaps,compare,eligible_students
from backend.solver import optimize,workforce,placement


def test_valid_baseline_and_hand_computed_metrics():
    data=generate(groups=1,per_group=2)
    assert validate(data)==[]
    result=metrics(data)
    # Each student: two days, 10-hour span, five teaching hours, five gap hours/day.
    assert result["gap_hours"]==20
    assert result["average_days"]==2
    assert result["average_span"]==600
    assert result["long_gap_2h"]==2
    assert result["score"]==45


def test_adjacent_meetings_do_not_overlap():
    assert not overlaps(Window(day=0,start=480,end=540),Window(day=0,start=540,end=600))


def test_diagnostic_fixture_has_real_conflicts_and_no_quality_score():
    result=metrics(generate("diagnostic",groups=1,per_group=40))
    assert not result["valid"] and result["score"] is None
    assert {"CAPACITY","STUDENT_OVERLAP","ROOM_OVERLAP","PROFESSOR_OVERLAP"} <= {i["code"] for i in result["issues"]}


def test_duration_prerequisites_and_availability():
    data=generate(groups=1,per_group=2)
    data.sections[0].meetings[0].end+=10
    data.students[0].completed=[]
    data.professors[0].availability=[]
    assert {"DURATION","PREREQUISITE","PROFESSOR_AVAILABILITY"} <= {i["code"] for i in validate(data)}


def test_duplicate_ids_and_cycles_rejected():
    raw=generate(groups=1,per_group=2).model_dump()
    raw["students"].append(raw["students"][0])
    with pytest.raises(ValueError): Semester.model_validate(raw)
    raw=generate(groups=1,per_group=2).model_dump()
    raw["courses"][0]["prerequisites"]=["C002"]
    raw["courses"][1]["prerequisites"]=["C001"]
    with pytest.raises(ValueError): Semester.model_validate(raw)


def test_solver_improves_with_bounded_changes():
    data=generate(groups=2,per_group=3)
    result=optimize(data,2,10)
    assert result["status"] in {"OPTIMAL","FEASIBLE"}
    candidate=Semester.model_validate(result["candidate"])
    assert not validate(candidate)
    assert len(result["comparison"]["changes"])<=2
    assert result["comparison"]["recovered_hours"]>0
    assert compare(data,candidate)==result["comparison"]


def test_zero_move_limit_and_invalid_baseline():
    data=generate(groups=1,per_group=2)
    result=optimize(data,0,5)
    assert result["status"] in {"OPTIMAL","FEASIBLE"}
    assert not result["comparison"]["changes"]
    assert optimize(generate("diagnostic",groups=1,per_group=2))["status"]=="INVALID_BASELINE"


def test_shortage_is_a_capacity_proof_not_a_timeout():
    data=generate("shortfall")
    assert not validate(data)
    signal=workforce(data)["signals"][0]
    assert signal["status"]=="PROVEN_CAPACITY_SHORTFALL"
    assert signal["minimum_unservable_sections"]==1
    assert signal["additional_minutes_needed"]==120
    assert signal["students_at_risk"]==112


def test_placement_eligibility_and_resources():
    data=generate(groups=1,per_group=2)
    assert not eligible_students(data,"C021") # already enrolled
    result=placement(data,"C030")
    assert result["eligible_count"]==2
    assert result["options"]
    option=result["options"][0]
    assert option["compatible_count"]==2
    assert option["seats_available"]==2
    data.students[0].completed=[]
    assert len(eligible_students(data,"C030"))==1


def test_policy_blocked_minutes_reduce_available_room_time():
    data=generate(groups=1,per_group=2)
    original=metrics(data)["room_utilization"]
    # No classes at noon in this fixture; remove that hour from room availability.
    data.policy.blocked=[Window(day=d,start=720,end=780) for d in range(5)]
    assert not validate(data)
    assert metrics(data)["room_utilization"]>original


def test_duplicate_course_enrollment_and_availability_rejected():
    raw=generate(groups=1,per_group=2).model_dump()
    raw["sections"][1]["course_id"]=raw["sections"][0]["course_id"]
    with pytest.raises(ValueError): Semester.model_validate(raw)
    raw=generate(groups=1,per_group=2).model_dump()
    raw["rooms"][0]["availability"].append(raw["rooms"][0]["availability"][0])
    with pytest.raises(ValueError): Semester.model_validate(raw)
