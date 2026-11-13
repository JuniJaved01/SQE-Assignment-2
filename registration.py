"""Student course registration system.

Reference implementation provided for SQE Assignment 2 testing.
Students should treat REQUIREMENTS.md as the source of expected behavior.
"""
from dataclasses import dataclass, field


@dataclass
class Student:
    student_id: str
    completed_courses: set[str] = field(default_factory=set)
    current_credits: int = 0
    outstanding_dues: int = 0
    registered_courses: set[str] = field(default_factory=set)


@dataclass
class Course:
    code: str
    credit_hours: int
    capacity: int
    enrolled: int = 0
    prerequisites: set[str] = field(default_factory=set)
    waitlist: list[str] = field(default_factory=list)


def check_credit_limit(current_credits: int, new_credits: int) -> bool:
    """Return whether an additional course can fit the permitted credit load."""
    if not 0 <= current_credits <= 18:
        raise ValueError("Invalid current credits")
    if not 1 <= new_credits <= 4:
        raise ValueError("Invalid course credits")
    return current_credits + new_credits <= 18  # FIX 1 (FR-01): was "< 18"; a total of exactly 18 is allowed


def prerequisites_satisfied(completed: set[str], required: set[str]) -> bool:
    """Return whether the completed-course record meets prerequisites."""
    if not required:
        return True
    return required.issubset(completed)  # FIX 2 (FR-03): was bool(completed.intersection(required)); EVERY prerequisite is needed


def registration_decision(student: Student, course: Course) -> str:
    """Evaluate registration without changing student or course state."""
    if student.outstanding_dues < 0:
        raise ValueError("Invalid dues")
    if not 0 <= course.enrolled <= course.capacity or course.capacity < 1:
        raise ValueError("Invalid capacity or enrollment")
    if student.outstanding_dues > 0:  # FIX 3 (FR-04): was "> 1000"; any positive dues blocks
        return "DUES_BLOCK"
    if course.code in student.registered_courses:
        return "ALREADY_REGISTERED"
    if not prerequisites_satisfied(student.completed_courses, course.prerequisites):
        return "PREREQUISITES_MISSING"
    if not check_credit_limit(student.current_credits, course.credit_hours):
        return "CREDIT_LIMIT"
    if course.enrolled == course.capacity:  # FIX 4 (FR-08): was "enrolled > capacity", which could never be true
        return "WAITLISTED"
    return "REGISTERED"


def register_course(student: Student, course: Course) -> str:
    """Apply a registration decision and update relevant records."""
    decision = registration_decision(student, course)
    if decision == "REGISTERED":
        student.registered_courses.add(course.code)
        student.current_credits += course.credit_hours
        course.enrolled += 1
    elif decision == "WAITLISTED" and student.student_id not in course.waitlist:
        course.waitlist.append(student.student_id)
    return decision


def withdraw_course(student: Student, course: Course) -> bool:
    """Withdraw an active registration; return whether removal occurred."""
    if course.code not in student.registered_courses:
        return False
    student.registered_courses.remove(course.code)
    student.current_credits -= course.credit_hours
    course.enrolled -= 1  # FIX 5 (FR-13): NEW line, free the seat when a student withdraws
    return True
