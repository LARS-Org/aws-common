"""
This script is used to run all the tests for the project.
"""

def do_run_tests(do_log_func, run_cmd_func):
    """
    Run all the tests for the project.
    """
    do_log_func("*** Running all tests for the project...")
    # python -m pytest tests/unit/
    run_cmd_func(["python", "-m", "pytest", "tests/unit/"])
    do_log_func("*** All tests passed.")