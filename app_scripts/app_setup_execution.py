"""
This script is used to automate the setup of the Python virtual environment, 
installation of Python requirements, and the application's deploy.
"""

import os
import subprocess
import sys


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


def setup_venv(execution_dir: str, script_dir: str):
    """
    Recreate the Python virtual environment by calling the `app_reset_venv.py` script.
    :param execution_dir: The directory to execute the script in.
    :param script_dir: The directory containing the `app_reset_venv.py` script.
    """
    script_path = os.path.join(script_dir, "app_reset_venv.py")
    print("*** Calling app_reset_venv.py script...")
    _run_command(f"python3.11 {script_path}", cwd=execution_dir, shell=True)
    print("*** Virtual environment recreated!")


def install_requirements(execution_dir: str, script_dir: str):
    """
    Install Python requirements by running the `app_install_reqs.py` script.
    :param execution_dir: The directory to execute the script in.
    :param script_dir: The directory containing the `app_install_reqs.py` script.
    """
    script_path = os.path.join(script_dir, "app_install_reqs.py")
    print("*** Calling app_install_reqs.py script...")
    _run_command(f"python3.11 {script_path}", cwd=execution_dir, shell=True)
    print("*** Python requirements installed!")


def deploy(execution_dir: str, script_dir: str):
    """
    Placeholder for the deploy functionality.
    :param execution_dir: The directory to execute the script in.
    :param script_dir: The directory containing the `app_install_reqs.py` script.
    """
    script_path = os.path.join(script_dir, "la_deploy.py")
    print("*** Calling la_deploy.py script...")
    _run_command(f"python3.11 {script_path}", cwd=execution_dir, shell=True)
    print("*** LA Deploy is done!")


def main():
    """
    Main function to parse command-line arguments and call the appropriate function.
    """
    error_msg_args = "Usage: la_setup.py --<setup_venv|install_requirements|deploy>"
    if len(sys.argv) != 4:
        print(error_msg_args)
        sys.exit(1)

    action = sys.argv[1]
    # Get the current script directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Get the caller script directory
    caller_dir = sys.argv[-1]

    # Map action to corresponding function
    if action in {"--setup_venv", "--setup", "--reset_venv", "setup_venv", "setup", "reset_venv"}:
        setup_venv(execution_dir=caller_dir, script_dir=current_dir)
        print("Please activate the virtual environment by running:")
        print(f"source {os.path.join(caller_dir, '.venv', 'bin', 'activate')}")
        # it will be commented while we don't solve the issue with the venv activation
        # install_requirements(execution_dir=caller_dir, script_dir=current_dir)
    elif action in {"--install_requirements", "--install", "--install_reqs", "install_requirements", "install", "install_reqs"}:
        install_requirements(execution_dir=caller_dir, script_dir=current_dir)
    elif action in {"--deploy", "--deploy_stack", "--deploy_cdk", "--deploy_app", "deploy", "deploy_stack", "deploy_cdk", "deploy_app"}:
        install_requirements(execution_dir=caller_dir, script_dir=current_dir)
        deploy(execution_dir=caller_dir, script_dir=current_dir)
    elif action in {"fast_deploy", "--fast_deploy"}:
        deploy(execution_dir=caller_dir, script_dir=current_dir)
    elif action in {"--help", "-h", "help"}:
        print("Automate the setup of the Python virtual environment, installation of Python requirements, and the application's deploy.")
        print("Usage: python3.11 la_setup.py --<setup_venv|install_requirements|deploy>")
        print("Examples:")
        print("python3.11 la_setup.py --setup_venv")
        print("python3.11 la_setup.py --install_requirements")
        print("python3.11 la_setup.py --deploy")
    else:
        print(f"Unknown action: {action}")
        print(error_msg_args)
        sys.exit(1)


if __name__ == "__main__":
    main()
