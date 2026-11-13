# tests/test_whitebox.py  (white-box tests: written AFTER reading registration.py; expected values still come from the SRS)
import pytest  # pytest gives us the test runner and raises()
from registration import Student, Course, registration_decision, register_course  # the code under test


def make(dues=0, credits=0, registered=(), cap=30, enrolled=0, waitlist=()):  # small helper that builds one student + one course
    s = Student("S001")  # create the student
    c = Course("CS201", 3, 30)  # create the course (3 credits, capacity 30)
    s.outstanding_dues = dues  # set dues
    s.current_credits = credits  # set current credits
    s.registered_courses = set(registered)  # set registered courses
    c.capacity = cap  # set capacity
    c.enrolled = enrolled  # set enrolled count
    c.waitlist = list(waitlist)  # set the waiting list
    return s, c  # give both objects to the test


# ---------- Gap-filling tests: line 50 decision (dues threshold), path P5 ----------
def test_WB01_dues_far_above_threshold_blocks():  # targets: line 50 TRUE branch, line 51 statement, path P5
    s, c = make(dues=2000)  # dues clearly above any threshold
    assert registration_decision(s, c) == "DUES_BLOCK"  # SRS FR-04: any dues > 0 blocks


def test_WB02_dues_equal_to_code_constant_blocks():  # targets: line 50 decision at its constant (1000); FR-04 says block
    s, c = make(dues=1000)  # exactly the constant used in the code
    assert registration_decision(s, c) == "DUES_BLOCK"  # SRS FR-04: any dues > 0 blocks


# ---------- MC/DC tests for line 48: (NOT (A and B)) OR C  with A: 0<=enrolled, B: enrolled<=capacity, C: capacity<1 ----------
MSG = "Invalid capacity or enrollment"  # the exact SRS message


def test_WB04_mcdc_row1_A_false():  # targets: A=False (B, C not evaluated) -> decision True
    s, c = make(cap=30, enrolled=-1)  # enrolled below zero
    with pytest.raises(ValueError) as info:  # error expected
        registration_decision(s, c)  # call the function
    assert str(info.value) == MSG  # exact message


def test_WB05_mcdc_row2_A_true_B_false():  # targets: A=True, B=False (C not evaluated) -> decision True
    s, c = make(cap=30, enrolled=31)  # enrolled above capacity
    with pytest.raises(ValueError) as info:  # error expected
        registration_decision(s, c)  # call the function
    assert str(info.value) == MSG  # exact message


def test_WB06_mcdc_row3_A_true_B_true_C_true():  # targets: A=True, B=True, C=True -> decision True
    s, c = make(cap=0, enrolled=0)  # capacity below one
    with pytest.raises(ValueError) as info:  # error expected
        registration_decision(s, c)  # call the function
    assert str(info.value) == MSG  # exact message


def test_WB07_mcdc_row4_all_false():  # targets: A=True, B=True, C=False -> decision False (no error)
    s, c = make(cap=30, enrolled=0)  # perfectly valid course
    assert registration_decision(s, c) == "REGISTERED"  # flow continues to the end


# ---------- path P9: line 58 TRUE branch -> line 59 (FR-08) ----------
def test_WB08_full_course_reaches_waitlist_return():  # targets: line 58 TRUE branch, line 59 statement, path P9
    s, c = make(cap=30, enrolled=30)  # full course (enrolled == capacity)
    assert registration_decision(s, c) == "WAITLISTED"  # SRS FR-08


# ---------- register_course line 70: decision == "WAITLISTED"  and  id not in waitlist ----------
def test_WB09_waitlist_append_X_true_Y_true():  # targets: X=True, Y=True -> line 71 executes
    s, c = make(enrolled=30)  # full course, student not on waitlist
    register_course(s, c)  # try to register
    assert c.waitlist == ["S001"]  # student appended once


def test_WB10_waitlist_no_append_X_true_Y_false():  # targets: X=True, Y=False -> line 71 skipped
    s, c = make(enrolled=30, waitlist=["S001"])  # full course, student already waiting
    register_course(s, c)  # try to register again
    assert c.waitlist == ["S001"]  # still exactly one entry


def test_WB11_no_waitlist_when_registered_X_false():  # targets: X=False (Y not evaluated) -> line 71 skipped
    s, c = make(enrolled=5)  # seats available
    assert register_course(s, c) == "REGISTERED"  # successful registration
    assert c.waitlist == []  # waitlist untouched
