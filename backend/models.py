"""Versioned domain contracts. Minutes and Sunday-based weekdays are explicit."""
from pydantic import BaseModel, Field, model_validator, ConfigDict


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Window(StrictModel):
    day: int = Field(ge=0, le=4)
    start: int = Field(ge=0, lt=1440)
    end: int = Field(gt=0, le=1440)

    @model_validator(mode="after")
    def ordered(self):
        if self.end <= self.start:
            raise ValueError("end must be after start")
        return self


class Course(StrictModel):
    id: str
    name: str
    name_ar: str
    department: str
    competency: str
    prerequisites: list[str] = []
    duration: int = Field(default=60, ge=30, le=240)
    meetings_per_week: int = Field(default=2, ge=1, le=5)
    room_type: str = "classroom"


class Student(StrictModel):
    id: str
    name: str
    cohort: str
    completed: list[str] = []
    sections: list[str] = []


class Professor(StrictModel):
    id: str
    name: str
    department: str
    competencies: list[str]
    contracted_minutes: int = Field(ge=0)
    availability: list[Window]


class Room(StrictModel):
    id: str
    name: str
    capacity: int = Field(gt=0)
    type: str = "classroom"
    availability: list[Window]


class Section(StrictModel):
    id: str
    course_id: str
    professor_id: str
    room_id: str
    capacity: int = Field(gt=0)
    meetings: list[Window] = Field(min_length=1)


class Demand(StrictModel):
    id: str
    course_id: str
    sections: int = Field(gt=0)
    students: list[str]


class Policy(StrictModel):
    version: str = "1.0"
    timezone: str = "Asia/Riyadh"
    open_minute: int = 480
    close_minute: int = 1080
    blocked: list[Window] = []
    allowed_starts: list[int] = [480, 540, 600, 660, 780, 840, 900, 960, 1020]
    weights: dict[str, int] = {"gaps": 30, "days": 18, "fairness": 14,
                               "load": 12, "simplicity": 8, "rooms": 10, "changes": 8}

    @model_validator(mode="after")
    def valid_policy(self):
        if not 0 <= self.open_minute < self.close_minute <= 1440:
            raise ValueError("invalid opening hours")
        if not self.allowed_starts or any(not self.open_minute <= v < self.close_minute for v in self.allowed_starts):
            raise ValueError("invalid allowed starts")
        if set(self.weights) != {"gaps", "days", "fairness", "load", "simplicity", "rooms", "changes"}:
            raise ValueError("all seven objective weights required")
        if any(v < 0 for v in self.weights.values()) or sum(self.weights.values()) != 100:
            raise ValueError("weights must be non-negative and sum to 100")
        return self


class Semester(StrictModel):
    schema_version: int = 1
    name: str
    kind: str = "imported"
    provenance: str
    seed: int = 2026
    courses: list[Course]
    students: list[Student]
    professors: list[Professor]
    rooms: list[Room]
    sections: list[Section]
    demands: list[Demand] = []
    policy: Policy = Field(default_factory=Policy)

    @model_validator(mode="after")
    def references(self):
        for key in ("courses", "students", "professors", "rooms", "sections", "demands"):
            values = getattr(self, key)
            if len({v.id for v in values}) != len(values):
                raise ValueError(f"duplicate {key} IDs")
        courses, sections = {c.id for c in self.courses}, {s.id for s in self.sections}
        professors, rooms = {p.id for p in self.professors}, {r.id for r in self.rooms}
        for c in self.courses:
            if not set(c.prerequisites) <= courses or c.id in c.prerequisites:
                raise ValueError("invalid prerequisite reference")
        graph = {c.id: c.prerequisites for c in self.courses}
        done, active = set(), set()
        def visit(cid):
            if cid in active:
                raise ValueError("cyclic prerequisites")
            if cid in done:
                return
            active.add(cid)
            for pre in graph[cid]:
                visit(pre)
            active.remove(cid)
            done.add(cid)
        for cid in courses:
            visit(cid)
        for s in self.sections:
            if s.course_id not in courses or s.professor_id not in professors or s.room_id not in rooms:
                raise ValueError("unknown section reference")
        for resource in [*self.professors, *self.rooms]:
            windows=sorted(resource.availability,key=lambda w:(w.day,w.start))
            for a,b in zip(windows,windows[1:]):
                if a.day==b.day and b.start<a.end:
                    raise ValueError("availability windows must not overlap")
        for student in self.students:
            if not set(student.sections) <= sections or not set(student.completed) <= courses:
                raise ValueError("unknown student reference")
            if len(student.sections) != len(set(student.sections)):
                raise ValueError("duplicate enrollment")
            student_courses=[next(s.course_id for s in self.sections if s.id==sid) for sid in student.sections]
            if len(set(student_courses))!=len(student_courses):
                raise ValueError("student cannot enroll in two sections of the same course")
        students = {s.id for s in self.students}
        for demand in self.demands:
            if demand.course_id not in courses or not set(demand.students) <= students:
                raise ValueError("unknown demand reference")
        return self
