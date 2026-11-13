# SQE Assignment 2: Student Course Registration System testing

Course: SE3002 Software Quality Engineering.
Team: Junaid Javed (22P-9163), Mian Ayan (22P-9149)

## Run the tests
```
pip install -r requirements.txt
python -m pytest tests/ -v
python -m pytest tests/ --cov=registration --cov-branch --cov-report=term-missing
```

## Contents
- registration.py: implementation under test (5 defects fixed in PR #8)
- tests/test_blackbox.py: black-box tests (ECP, BVA, decision table, state tests)
- tests/test_whitebox.py: white-box tests (MC/DC, branch and path tests)
- docs/: test design sheets, decision table, cfg.png, testing_report.pdf
- .github/workflows/tests.yml: GitHub Actions workflow (pytest with coverage)

## Branches and pull requests
- blackbox-testing: PR #1
- whitebox-testing: PR #7
- defect-fixes: PR #8 (closes Issues #2 to #6)
