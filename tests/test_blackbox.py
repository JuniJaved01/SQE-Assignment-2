# tests/test_blackbox.py  (black-box tests: expected values come ONLY from REQUIREMENTS.md)
import pytest  # pytest gives us the test runner, parametrize and raises()
from registration import (  # import the functions and classes the SRS names
    Student,  # the Student class
    Course,  # the Course class
    check_credit_limit,  # FR-01, FR-02
    prerequisites_satisfied,  # FR-03
    registration_decision,  # FR-04 to FR-10, FR-15
    register_course,  # FR-11, FR-12
    withdraw_course,  # FR-13, FR-14
)  # end of the import list


def make(dues=0, credits=0, completed=(), registered=(), c_credits=3, cap=30, enrolled=0, prereqs=(), waitlist=()):  # builds one student + one course
    s = Student("S001")  # create a student (constructor call copied from README)
    c = Course("CS201", 3, 30)  # create a course (constructor call copied from README)
    s.outstanding_dues = dues  # set dues (SRS data model)
    s.current_credits = credits  # set current credits (SRS data model)
    s.completed_courses = set(completed)  # set completed courses
    s.registered_courses = set(registered)  # set already-registered courses
    c.credit_hours = c_credits  # set the course credit hours
    c.capacity = cap  # set the course capacity
    c.enrolled = enrolled  # set how many are enrolled
    c.prerequisites = set(prereqs)  # set the course prerequisites
    c.waitlist = list(waitlist)  # set the waiting list
    return s, c  # hand both objects back to the test


def snap(s, c):  # takes a "photo" of every field so we can compare before/after
    return (s.student_id, set(s.completed_courses), s.current_credits, s.outstanding_dues, set(s.registered_courses),  # student fields
            c.code, c.credit_hours, c.capacity, c.enrolled, set(c.prerequisites), list(c.waitlist))  # course fields


# ---------- registration_decision cases: ID lists every technique row that this one test covers ----------
DECISION_CASES = [  # each entry: (inputs for make(), expected status)
    pytest.param({}, "REGISTERED", id="ECP-02|ECP-05|BVA-14|DT-06"),  # clean student: dues 0, no prereqs
    pytest.param({"dues": 500}, "DUES_BLOCK", id="ECP-01|DT-01"),  # positive dues
    pytest.param({"dues": 1}, "DUES_BLOCK", id="BVA-13"),  # dues just above zero
    pytest.param({"registered": ["CS201"]}, "ALREADY_REGISTERED", id="ECP-04|DT-02"),  # already in the course
    pytest.param({"completed": ["CS101"], "prereqs": ["CS101", "MATH101"]}, "PREREQUISITES_MISSING", id="ECP-07|DT-03"),  # some prereqs missing
    pytest.param({"completed": [], "prereqs": ["CS101", "MATH101"]}, "PREREQUISITES_MISSING", id="ECP-08"),  # no prereq completed
    pytest.param({"completed": ["CS101", "MATH101"], "prereqs": ["CS101", "MATH101"]}, "REGISTERED", id="ECP-06"),  # all prereqs done
    pytest.param({"credits": 10, "c_credits": 3}, "REGISTERED", id="ECP-09"),  # 13 total, within limit
    pytest.param({"credits": 16, "c_credits": 3}, "CREDIT_LIMIT", id="ECP-10|DT-04"),  # 19 total, over limit
    pytest.param({"enrolled": 10}, "REGISTERED", id="ECP-11"),  # seats available
    pytest.param({"enrolled": 30}, "WAITLISTED", id="ECP-12|BVA-17|DT-05"),  # course full
    pytest.param({"enrolled": 29}, "REGISTERED", id="BVA-16"),  # one seat left
    pytest.param({"cap": 1, "enrolled": 0}, "REGISTERED", id="BVA-20"),  # smallest course, empty
    pytest.param({"cap": 1, "enrolled": 1}, "WAITLISTED", id="BVA-21"),  # smallest course, full
    pytest.param({"credits": 14, "c_credits": 4}, "REGISTERED", id="BVA-23"),  # total exactly 18
    pytest.param({"credits": 15, "c_credits": 4}, "CREDIT_LIMIT", id="BVA-24"),  # total 19
    pytest.param({"credits": 18, "c_credits": 1}, "CREDIT_LIMIT", id="BVA-25"),  # student already at max
    pytest.param({"credits": 0, "c_credits": 1}, "REGISTERED", id="BVA-26"),  # smallest possible total
    pytest.param({"dues": 500, "registered": ["CS201"], "completed": [], "prereqs": ["CS101"], "credits": 18, "enrolled": 30}, "DUES_BLOCK", id="DT-07"),  # everything wrong -> dues wins
    pytest.param({"registered": ["CS201"], "completed": [], "prereqs": ["CS101"], "credits": 18, "enrolled": 30}, "ALREADY_REGISTERED", id="DT-08"),  # already-registered beats prereq/credit/full
    pytest.param({"completed": [], "prereqs": ["CS101"], "credits": 18, "enrolled": 30}, "PREREQUISITES_MISSING", id="DT-09"),  # prereq beats credit/full
    pytest.param({"credits": 18, "enrolled": 30}, "CREDIT_LIMIT", id="DT-10"),  # credit beats full
    pytest.param({"dues": 500, "enrolled": 30}, "DUES_BLOCK", id="DT-11"),  # dues beats waitlist
]  # end of decision cases


@pytest.mark.parametrize("kwargs, expected", DECISION_CASES)  # run the test once per row above
def test_registration_decision(kwargs, expected):  # checks the returned status string
    s, c = make(**kwargs)  # build the objects for this row
    assert registration_decision(s, c) == expected  # compare with the SRS-derived answer


# ---------- registration_decision error cases (FR-15) ----------
ERROR_CASES = [  # each entry: (inputs for make(), exact error message)
    pytest.param({"dues": -100}, "Invalid dues", id="ECP-03"),  # clearly negative dues
    pytest.param({"dues": -1}, "Invalid dues", id="BVA-15"),  # dues just below zero
    pytest.param({"cap": 0}, "Invalid capacity or enrollment", id="ECP-15|BVA-22"),  # capacity below 1
    pytest.param({"cap": 30, "enrolled": 31}, "Invalid capacity or enrollment", id="BVA-18"),  # enrolled just above capacity
    pytest.param({"cap": 30, "enrolled": -1}, "Invalid capacity or enrollment", id="BVA-19"),  # enrolled just below zero
    pytest.param({"dues": -1, "cap": 0}, "Invalid dues", id="DT-12"),  # both invalid -> dues is validated first
]  # end of error cases


@pytest.mark.parametrize("kwargs, message", ERROR_CASES)  # run once per row
def test_registration_decision_errors(kwargs, message):  # checks the exception type and text
    s, c = make(**kwargs)  # build the objects
    with pytest.raises(ValueError) as info:  # we EXPECT a ValueError here
        registration_decision(s, c)  # call the function under test
    assert str(info.value) == message  # the message must match the SRS exactly


# ---------- check_credit_limit (FR-01, FR-02) ----------
CREDIT_CASES = [  # each entry: (current, new, expected True/False)
    pytest.param(0, 1, True, id="BVA-01"),  # both at their minimum
    pytest.param(0, 4, True, id="BVA-02"),  # new credits at maximum
    pytest.param(14, 4, True, id="BVA-03"),  # total exactly 18
    pytest.param(15, 4, False, id="BVA-04"),  # total 19
    pytest.param(15, 3, True, id="BVA-05"),  # SRS scenario 1, total 18
    pytest.param(16, 3, False, id="BVA-06"),  # SRS scenario 2, total 19
    pytest.param(17, 1, True, id="BVA-07"),  # total exactly 18
    pytest.param(18, 1, False, id="BVA-08"),  # current at max, total 19
]  # end of credit cases


@pytest.mark.parametrize("current, new, expected", CREDIT_CASES)  # run once per row
def test_check_credit_limit(current, new, expected):  # checks True/False result
    assert check_credit_limit(current, new) is expected  # must be exactly True or False


CREDIT_ERROR_CASES = [  # each entry: (current, new, exact message)
    pytest.param(-1, 3, "Invalid current credits", id="BVA-09"),  # current just below 0
    pytest.param(19, 3, "Invalid current credits", id="ECP-14|BVA-10"),  # current just above 18
    pytest.param(10, 0, "Invalid course credits", id="BVA-11"),  # new credits just below 1
    pytest.param(10, 5, "Invalid course credits", id="ECP-13|BVA-12"),  # new credits just above 4
    pytest.param(19, 5, "Invalid current credits", id="ECP-19"),  # both bad -> current is checked first
]  # end of credit error cases


@pytest.mark.parametrize("current, new, message", CREDIT_ERROR_CASES)  # run once per row
def test_check_credit_limit_errors(current, new, message):  # checks the exception
    with pytest.raises(ValueError) as info:  # we EXPECT a ValueError
        check_credit_limit(current, new)  # call the function under test
    assert str(info.value) == message  # the message must match the SRS exactly


# ---------- prerequisites_satisfied (FR-03) ----------
def test_ECP16_prereq_function_empty_required():  # no prerequisites required
    assert prerequisites_satisfied({"CS101"}, set()) is True  # empty requirement is always satisfied


def test_ECP17_prereq_function_all_present():  # every required course completed
    assert prerequisites_satisfied({"CS101", "MATH101", "PHY101"}, {"CS101", "MATH101"}) is True  # extras are fine


def test_ECP18_prereq_function_some_missing():  # one required course missing
    assert prerequisites_satisfied({"CS101"}, {"CS101", "MATH101"}) is False  # needs EVERY course


# ---------- state changes (FR-10 to FR-14) ----------
def test_ST01_register_success_changes_state():  # successful registration
    s, c = make(credits=3, enrolled=5)  # student has 3 credits, course has 5 enrolled
    result = register_course(s, c)  # try to register
    assert result == "REGISTERED"  # status must be REGISTERED
    assert "CS201" in s.registered_courses  # course code was added
    assert s.current_credits == 6  # credits went 3 -> 6
    assert c.enrolled == 6  # enrolled went 5 -> 6
    assert c.waitlist == []  # nobody was waitlisted


def test_ST02_register_waitlisted_changes_only_waitlist():  # full course
    s, c = make(credits=3, enrolled=30)  # course is full
    result = register_course(s, c)  # try to register
    assert result == "WAITLISTED"  # status must be WAITLISTED
    assert c.waitlist == ["S001"]  # student ID was appended
    assert s.current_credits == 3  # credits unchanged
    assert s.registered_courses == set()  # not registered
    assert c.enrolled == 30  # enrollment unchanged


def test_ST03_waitlist_no_duplicate_entry():  # FR-12: append only if absent
    s, c = make(enrolled=30)  # course is full
    register_course(s, c)  # first attempt joins the waitlist
    register_course(s, c)  # second attempt must not add again
    assert c.waitlist.count("S001") == 1  # exactly one entry


FAIL_CASES = [  # each entry: (inputs for make(), expected status)
    pytest.param({"dues": 500, "credits": 3, "enrolled": 5}, "DUES_BLOCK", id="ST04"),  # dues block
    pytest.param({"registered": ["CS201"], "credits": 3, "enrolled": 5}, "ALREADY_REGISTERED", id="ST05"),  # duplicate registration
    pytest.param({"prereqs": ["CS101"], "credits": 3, "enrolled": 5}, "PREREQUISITES_MISSING", id="ST06"),  # prereq missing
    pytest.param({"credits": 16, "enrolled": 5}, "CREDIT_LIMIT", id="ST07"),  # over credit limit
]  # end of failing-operation cases


@pytest.mark.parametrize("kwargs, expected", FAIL_CASES)  # run once per row
def test_ST_failed_registration_changes_nothing(kwargs, expected):  # FR-12 last sentence
    s, c = make(**kwargs)  # build the objects
    before = snap(s, c)  # photo before
    assert register_course(s, c) == expected  # status must match the SRS
    assert snap(s, c) == before  # photo after must be identical


@pytest.mark.parametrize("kwargs", [pytest.param({}, id="ST08a"), pytest.param({"enrolled": 30}, id="ST08b")])  # eligible and full
def test_ST08_decision_does_not_mutate(kwargs):  # FR-10
    s, c = make(**kwargs)  # build the objects
    before = snap(s, c)  # photo before
    registration_decision(s, c)  # decision only, must not change anything
    assert snap(s, c) == before  # photo after must be identical


def test_ST09_withdraw_enrolled_student():  # FR-13
    s, c = make(credits=6, registered=["CS201"], enrolled=5)  # student is in the course
    assert withdraw_course(s, c) is True  # withdrawal succeeds
    assert "CS201" not in s.registered_courses  # course removed
    assert s.current_credits == 3  # 6 - 3 credit hours
    assert c.enrolled == 4  # enrolled decremented by one


def test_ST10_withdraw_not_registered_changes_nothing():  # FR-14
    s, c = make(credits=6, enrolled=5)  # student is NOT in the course
    before = snap(s, c)  # photo before
    assert withdraw_course(s, c) is False  # withdrawal refused
    assert snap(s, c) == before  # nothing changed
