"""
This script is used to automate the setup of the Python virtual environment, 
installation of Python requirements, and the application's deploy.
"""
import os
import subprocess
import sys


def _run_command(command, cwd=None):
    """
    Run a shell command in the specified directory.

    :param command: The command to run.
    :param cwd: The directory to run the command in.
    """
    result = subprocess.run(command, shell=True, cwd=cwd)
    if result.returncode != 0:
        sys.exit(result.returncode)


def setup_venv(current_dir: str, script_dir: str):
    """
    Recreate the Python virtual environment by calling the `la_setup_venv.py` script.

    :param current_dir: The current directory of this script.
    :param script_dir: The directory containing the `la_setup_venv.py` script.
    """
    script_path = os.path.join(script_dir, 'la_setup_venv.py')
    print("*** Calling la_setup_venv.py script...")
    _run_command(f"python3.11 {script_path}", cwd=current_dir)
    print("*** Virtual environment recreated!")


def install_requirements(current_dir: str, script_dir: str):
    """
    Install Python requirements by running the `la_install_reqs.py` script.
    
    :param current_dir: The current directory of this script.
    :param script_dir: The directory containing the `la_install_reqs.py` script.
    """
    script_path = os.path.join(script_dir, 'la_install_reqs.py')
    print("*** Calling la_install_reqs.py script...")
    _run_command(f"python3.11 {script_path}", cwd=current_dir)
    print("*** Python requirements installed!")


def deploy(current_dir: str, script_dir: str):
    """
    Placeholder for the deploy functionality.
    """
    script_path = os.path.join(script_dir, 'la_deploy.py')
    print("*** Calling la_deploy.py script...")
    _run_command(f"python3.11 {script_path}", cwd=current_dir)
    print("*** LA Deploy is done!")


def main():
    """
    Main function to parse command-line arguments and call the appropriate function.
    """
    error_msg_args = "Usage: la_setup.py --<setup_venv|install_requirements|deploy>"
    if len(sys.argv) != 2:
        print(error_msg_args)
        sys.exit(1)

    action = sys.argv[1]
    # Get the current script directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Construct path to sibling directory
    script_dir = os.path.join(current_dir, '..', 'la-common')
   
    # check if script directory exists
    if not os.path.exists(script_dir):
        print(f"Script directory not found: {script_dir}")
        # call the git clone command
        parent_dir = os.path.join(current_dir, '..')
        _run_command(f"git clone https://github.com/LearnAnything-Organization/la-common.git", cwd=parent_dir)
        print(f"Cloned the la-common repository to {script_dir}")
    # script directory exists, update it
    # call the git pull command to ensure the latest version
    _run_command("git fetch", cwd=script_dir)
    _run_command("git pull", cwd=script_dir)
    print(f"Updated the la-common repository at {script_dir}")

    # Map action to corresponding function
    if action == "--setup_venv":
        setup_venv(current_dir, script_dir)
    elif action == "--install_requirements":
        install_requirements(current_dir, script_dir)
    elif action == "--deploy":
        deploy(current_dir, script_dir)
    else:
        print(f"Unknown action: {action}")
        print(error_msg_args)
        sys.exit(1)


if __name__ == "__main__":
    main()
