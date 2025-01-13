"""Recreates the Python virtual environment for the project."""

import os
import shutil

# The directory where the Python virtual environment is stored
PYTHON_VENV_DIR = "venv"


def do_reset_venv(do_log_func, run_cmd_func):
    """
    Recreate the Python virtual environment.
    """
    do_log_func(f"*** Deleting all content under {PYTHON_VENV_DIR}...")
    shutil.rmtree(PYTHON_VENV_DIR, ignore_errors=True)

    do_log_func("*** Recreating Python virtual environment...")
    run_cmd_func(["python3.11", "-m", "venv", PYTHON_VENV_DIR])

    activate_script = os.path.join(PYTHON_VENV_DIR, "bin", "activate")

    # warn the user to activate the virtual environment
    print("*** Virtual environment recreated! Please activate it by running:")
    print(f"source {activate_script}")
