"""Recreates the Python virtual environment for the project."""

import os
import shutil

# The directory where the Python virtual environment is stored
DEFAULT_PYTHON_VENV_DIR = "venv"
CUSTOM_PYTHON_VENV_DIR = DEFAULT_PYTHON_VENV_DIR
if os.getenv("AWS_COMMON_PYTHON_VENV_DIR"):
    CUSTOM_PYTHON_VENV_DIR = os.getenv("AWS_COMMON_PYTHON_VENV_DIR")
    print(f"Using Python virtual environment directory: {CUSTOM_PYTHON_VENV_DIR}")


def do_reset_venv(do_log_func, run_cmd_func, ignore_central_venv=False):
    """
    Recreate the Python virtual environment.
    """
    # If ignore_central_venv is True, do not use the centralized venv configuration
    if ignore_central_venv:
        do_log_func("Ignoring centralized virtual environment configuration.")
        venv_dir = DEFAULT_PYTHON_VENV_DIR
    else:
        venv_dir = CUSTOM_PYTHON_VENV_DIR

    do_log_func(f"*** Deleting all content under {venv_dir}...")
    shutil.rmtree(venv_dir, ignore_errors=True)

    do_log_func("*** Recreating Python virtual environment...")
    run_cmd_func(["python3.11", "-m", "venv", venv_dir])

    activate_script = os.path.join(venv_dir, "bin", "activate")

    # warn the user to activate the virtual environment
    print("*** Virtual environment recreated! Please activate it by running:")
    print(f"source {activate_script}")
