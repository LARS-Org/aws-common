"""Recreates the Python virtual environment for the project."""
import os
import shutil
import subprocess
import sys
import tempfile


def _run_command(command, cwd=None, shell=False):
    """
    Run a shell command in the specified directory.

    :param command: The command to run.
    :param cwd: The directory to run the command in.
    :param shell: Whether to use a shell to run the command.
    """
    result = subprocess.run(command, shell=shell, cwd=cwd)
    if result.returncode != 0:
        sys.exit(result.returncode)   

def reset_venv():
    PYTHON_VENV_DIR = ".venv"

    print(f"*** Deleting all content under {PYTHON_VENV_DIR}...")
    shutil.rmtree(PYTHON_VENV_DIR, ignore_errors=True)

    print("*** Recreating Python virtual environment...")
    _run_command(["python3.11", "-m", "venv", PYTHON_VENV_DIR])

    print("*** Activating Python virtual environment...")
    activate_script = os.path.join(PYTHON_VENV_DIR, "bin", "activate")


    # Create a temporary shell script to activate the virtual environment
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sh') as temp_script:
        temp_script.write(f"#!/bin/bash\n")
        temp_script.write(f"source {activate_script}\n")
        temp_script.write(f"exec $SHELL\n")
        temp_script_path = temp_script.name

    # Make the script executable
    os.chmod(temp_script_path, 0o775)

    # Execute the temporary shell script
    subprocess.run(f"bash {temp_script_path}", shell=True)

    # remove the temporary shell script
    os.remove(temp_script_path)
    
    # warn the user to activate the virtual environment
    print("*** Virtual environment recreated! Please activate it by running:")
    print(f"source {activate_script}")


if __name__ == "__main__":
    reset_venv()
