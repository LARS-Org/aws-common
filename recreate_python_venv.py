"""Recreates the Python virtual environment for the project."""

import os
import subprocess
import sys
import shutil


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


def main():
    PYTHON_VENV_DIR = ".venv/"

    print(f"*** Deleting all content under {PYTHON_VENV_DIR}...")
    shutil.rmtree(PYTHON_VENV_DIR, ignore_errors=True)

    print("*** Recreating Python virtual environment...")
    _run_command(["python3.11", "-m", "venv", ".venv"])

    print("*** Activating Python virtual environment...")
    activate_script = os.path.join(PYTHON_VENV_DIR, "bin", "activate")
    print(f"*** Activate script: {activate_script}")

    # Use bash explicitly to source the activation script
    bash_command = f"bash -c 'source {activate_script}'"
    _run_command(bash_command, shell=True)

    print("*** Installing Python requirements...")
    os.chmod("install-python-requirements.sh", 0o755)
    _run_command(["./install-python-requirements.sh"])

    print("*** All done!!!")


if __name__ == "__main__":
    main()
